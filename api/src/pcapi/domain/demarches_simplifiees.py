from collections.abc import Sequence
from datetime import datetime
import logging
from typing import Optional

from pcapi import settings
from pcapi.connectors import api_demarches_simplifiees
from pcapi.domain.bank_account import format_raw_iban_and_bic
from pcapi.domain.bank_information import CannotRegisterBankInformation
from pcapi.models.bank_information import BankInformationStatus
from pcapi.repository.beneficiary_import_queries import get_already_processed_applications_ids
from pcapi.utils.date import DATE_ISO_FORMAT


logger = logging.getLogger(__name__)


FIELD_FOR_VENUE_WITH_SIRET = (
    "Si vous souhaitez renseigner les coordonn\u00e9es bancaires d'un lieu avec SIRET, merci de saisir son SIRET :"
)
FIELD_FOR_VENUE_WITHOUT_SIRET = "Si vous souhaitez renseigner les coordonn\u00e9es bancaires d'un lieu sans SIRET, merci de saisir le \"Nom du lieu\", \u00e0 l'identique de celui dans le pass Culture Pro :"

ACCEPTED_DMS_STATUS = (api_demarches_simplifiees.DmsApplicationStates.closed,)
DRAFT_DMS_STATUS = (
    api_demarches_simplifiees.DmsApplicationStates.received,
    api_demarches_simplifiees.DmsApplicationStates.initiated,
)
REJECTED_DMS_STATUS = (
    api_demarches_simplifiees.DmsApplicationStates.refused,
    api_demarches_simplifiees.DmsApplicationStates.without_continuation,
)


class ApplicationDetail:
    def __init__(
        self,
        siren: str,
        status: BankInformationStatus,
        application_id: int,
        iban: str,
        bic: str,
        modification_date: datetime,
        siret: Optional[str] = None,
        venue_name: Optional[str] = None,
    ):
        self.siren = siren
        self.status = status
        self.application_id = application_id
        self.iban = iban
        self.bic = bic
        self.siret = siret
        self.venue_name = venue_name
        self.modification_date = modification_date


def get_all_application_ids_for_demarche_simplifiee(
    procedure_id: str,
    token: str,
    last_update: datetime = None,
    accepted_states: Sequence[api_demarches_simplifiees.DmsApplicationStates] = tuple(
        api_demarches_simplifiees.DmsApplicationStates
    ),
) -> list[int]:
    current_page = 1
    number_of_pages = 1
    applications = []

    while current_page <= number_of_pages:
        api_response = api_demarches_simplifiees.get_all_applications_for_procedure(
            procedure_id, token, page=current_page, results_per_page=100
        )
        number_of_pages = api_response["pagination"]["nombre_de_page"]
        logger.info("[IMPORT DEMARCHES SIMPLIFIEES] page %i of %i", current_page, number_of_pages)

        applications_to_process = [
            application
            for application in api_response["dossiers"]
            if _has_requested_state(application, accepted_states) and _was_last_updated_after(application, last_update)
        ]
        logger.info("[IMPORT DEMARCHES SIMPLIFIEES] %i applications to process", len(applications_to_process))
        applications += applications_to_process

        current_page += 1

    logger.info("[IMPORT DEMARCHES SIMPLIFIEES] Total : %i applications", len(applications))

    return [application["id"] for application in _sort_applications_by_date(applications)]


def get_closed_application_ids_for_demarche_simplifiee(procedure_id: int, token: str) -> list[int]:
    assert settings.DMS_TOKEN
    application_ids = set(
        get_all_application_ids_for_demarche_simplifiee(
            str(procedure_id), settings.DMS_TOKEN, last_update=None, accepted_states=ACCEPTED_DMS_STATUS
        )
    )
    existing_applications_id = get_already_processed_applications_ids(procedure_id)
    return sorted(application_ids - existing_applications_id)


def get_received_application_ids_for_demarche_simplifiee(
    procedure_id: str, token: str, last_update: datetime
) -> list[int]:
    return get_all_application_ids_for_demarche_simplifiee(
        procedure_id, token, last_update, accepted_states=DRAFT_DMS_STATUS
    )


def get_offerer_bank_information_application_details_by_application_id(application_id: str) -> ApplicationDetail:
    assert settings.DMS_OFFERER_PROCEDURE_ID
    assert settings.DMS_TOKEN
    response_application_details = api_demarches_simplifiees.get_application_details(
        application_id, procedure_id=settings.DMS_OFFERER_PROCEDURE_ID, token=settings.DMS_TOKEN
    )

    application_details = ApplicationDetail(
        siren=response_application_details["dossier"]["entreprise"]["siren"],
        status=_get_status_from_demarches_simplifiees_application_state(
            response_application_details["dossier"]["state"]
        ),
        application_id=int(response_application_details["dossier"]["id"]),
        iban=format_raw_iban_and_bic(_find_value_in_fields(response_application_details["dossier"]["champs"], "IBAN")),
        bic=format_raw_iban_and_bic(_find_value_in_fields(response_application_details["dossier"]["champs"], "BIC")),
        modification_date=datetime.strptime(response_application_details["dossier"]["updated_at"], DATE_ISO_FORMAT),
    )
    return application_details


def parse_raw_bic_data(data: dict) -> dict:
    result = {
        "status": data["dossier"]["state"],
        "updated_at": data["dossier"]["dateDerniereModification"],
    }
    ID_TO_NAME_MAPPING = {
        "Q2hhbXAtNDA3ODg5": "firstname",
        "Q2hhbXAtNDA3ODkw": "lastname",
        "Q2hhbXAtNDA3ODky": "phone_number",
        "Q2hhbXAtMzUyNzIy": "iban",
        "Q2hhbXAtMzUyNzI3": "bic",
    }
    for field in data["dossier"]["champs"]:
        if field["id"] in ID_TO_NAME_MAPPING:
            result[ID_TO_NAME_MAPPING[field["id"]]] = field["value"]
        elif field["id"] == "Q2hhbXAtNzgyODAw":
            result["siret"] = field["etablissement"]["siret"]
            result["siren"] = field["etablissement"]["entreprise"]["siren"]
    return result


def get_venue_bank_information_application_details_by_application_id(
    application_id: str, version: int = 1
) -> ApplicationDetail:
    if version == 1:
        assert settings.DMS_VENUE_PROCEDURE_ID
        assert settings.DMS_TOKEN
        response_application_details = api_demarches_simplifiees.get_application_details(
            application_id, procedure_id=settings.DMS_VENUE_PROCEDURE_ID, token=settings.DMS_TOKEN
        )

        application_details = ApplicationDetail(
            siren=response_application_details["dossier"]["entreprise"]["siren"],
            status=_get_status_from_demarches_simplifiees_application_state(
                response_application_details["dossier"]["state"]
            ),
            application_id=int(response_application_details["dossier"]["id"]),
            iban=format_raw_iban_and_bic(
                _find_value_in_fields(response_application_details["dossier"]["champs"], "IBAN")
            ),
            bic=format_raw_iban_and_bic(
                _find_value_in_fields(response_application_details["dossier"]["champs"], "BIC")
            ),
            siret=_find_value_in_fields(response_application_details["dossier"]["champs"], FIELD_FOR_VENUE_WITH_SIRET),
            venue_name=_find_value_in_fields(
                response_application_details["dossier"]["champs"], FIELD_FOR_VENUE_WITHOUT_SIRET
            ),
            modification_date=datetime.strptime(response_application_details["dossier"]["updated_at"], DATE_ISO_FORMAT),
        )
        return application_details
    if version == 2:
        client = api_demarches_simplifiees.DMSGraphQLClient()
        raw_data = client.get_bic(int(application_id))
        data = parse_raw_bic_data(raw_data["data"])
        return ApplicationDetail(
            siren=data["siren"],
            status=data["status"],
            application_id=int(application_id),
            iban=data["iban"],
            bic=data["bic"],
            siret=data["siret"],
            modification_date=data["updated_at"],
        )
    raise ValueError("Unknown version %s" % version)


def _has_requested_state(application: dict, states: Sequence[api_demarches_simplifiees.DmsApplicationStates]) -> bool:
    return api_demarches_simplifiees.DmsApplicationStates[application["state"]] in states


def _was_last_updated_after(application: dict, last_update: datetime = None) -> bool:
    if not last_update:
        return True
    return datetime.strptime(application["updated_at"], DATE_ISO_FORMAT) >= last_update


def _sort_applications_by_date(applications: list) -> list:
    return sorted(applications, key=lambda application: datetime.strptime(application["updated_at"], DATE_ISO_FORMAT))


def _get_status_from_demarches_simplifiees_application_state(state: str) -> BankInformationStatus:
    try:
        dms_state = api_demarches_simplifiees.DmsApplicationStates[state]
    except KeyError:
        raise CannotRegisterBankInformation(f"Unknown Demarches Simplifiées state {state}")
    rejected_states = REJECTED_DMS_STATUS
    accepted_states = ACCEPTED_DMS_STATUS
    draft_states = DRAFT_DMS_STATUS
    if dms_state in rejected_states:
        return BankInformationStatus.REJECTED
    if dms_state in accepted_states:
        return BankInformationStatus.ACCEPTED
    if dms_state in draft_states:
        return BankInformationStatus.DRAFT
    raise ValueError(f"Unexpected DMS status: '{state}'")


def _find_value_in_fields(fields: list[dict], value_name: str) -> Optional[dict]:
    for field in fields:
        if field["type_de_champ"]["libelle"] == value_name:
            return field["value"]
    return None
