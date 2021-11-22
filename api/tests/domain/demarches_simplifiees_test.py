from datetime import datetime
from unittest.mock import call
from unittest.mock import patch

import pytest

from pcapi.connectors.api_demarches_simplifiees import DmsApplicationStates
from pcapi.domain.demarches_simplifiees import ApplicationDetail
from pcapi.domain.demarches_simplifiees import CannotRegisterBankInformation
from pcapi.domain.demarches_simplifiees import _get_status_from_demarches_simplifiees_application_state
from pcapi.domain.demarches_simplifiees import get_all_application_ids_for_demarche_simplifiee
from pcapi.domain.demarches_simplifiees import get_closed_application_ids_for_demarche_simplifiee
from pcapi.domain.demarches_simplifiees import get_offerer_bank_information_application_details_by_application_id
from pcapi.domain.demarches_simplifiees import get_venue_bank_information_application_details_by_application_id
from pcapi.domain.demarches_simplifiees import parse_raw_bic_data
from pcapi.models.bank_information import BankInformationStatus
from pcapi.utils.date import DATE_ISO_FORMAT

from tests.connector_creators.demarches_simplifiees_creators import (
    offerer_demarche_simplifiee_application_detail_response,
)
from tests.connector_creators.demarches_simplifiees_creators import (
    venue_demarche_simplifiee_application_detail_response_with_siret,
)
from tests.connector_creators.demarches_simplifiees_creators import (
    venue_demarche_simplifiee_application_detail_response_without_siret,
)


@patch("pcapi.connectors.api_demarches_simplifiees.get_all_applications_for_procedure")
class GetAllApplicationIdsForBeneficiaryImportTest:
    def setup_method(self):
        self.PROCEDURE_ID = "123456789"
        self.TOKEN = "AZERTY123/@.,!é"

    def test_returns_applications_from_all_pages(self, get_all_applications_for_procedure):
        # Given
        get_all_applications_for_procedure.side_effect = [
            {
                "dossiers": [
                    {"id": 1, "updated_at": "2018-02-05T16:51:18.293Z", "state": "closed"},
                    {"id": 2, "updated_at": "2019-02-05T16:51:18.293Z", "state": "closed"},
                    {"id": 3, "updated_at": "2019-02-03T16:51:18.293Z", "state": "closed"},
                ],
                "pagination": {"page": 1, "resultats_par_page": 3, "nombre_de_page": 2},
            },
            {
                "dossiers": [
                    {"id": 4, "updated_at": "2019-02-04T16:51:18.293Z", "state": "closed"},
                    {"id": 5, "updated_at": "2019-02-01T16:51:18.293Z", "state": "closed"},
                ],
                "pagination": {"page": 2, "resultats_par_page": 3, "nombre_de_page": 2},
            },
        ]

        # When
        application_ids = get_all_application_ids_for_demarche_simplifiee(self.PROCEDURE_ID, self.TOKEN)

        # Then
        assert application_ids == [1, 5, 3, 4, 2]

    def test_returns_applications_with_all_states_by_default(self, get_all_applications_for_procedure):
        # Given
        get_all_applications_for_procedure.return_value = {
            "dossiers": [
                {"id": 1, "updated_at": "2019-02-04T16:51:18.293Z", "state": "closed"},
                {"id": 2, "updated_at": "2019-02-04T16:51:18.293Z", "state": "initiated"},
                {"id": 3, "updated_at": "2019-02-03T16:51:18.293Z", "state": "refused"},
                {"id": 4, "updated_at": "2019-02-03T16:51:18.293Z", "state": "received"},
                {"id": 5, "updated_at": "2019-02-03T16:51:18.293Z", "state": "without_continuation"},
            ],
            "pagination": {"page": 1, "resultats_par_page": 100, "nombre_de_page": 1},
        }

        # When
        application_ids = get_all_application_ids_for_demarche_simplifiee(self.PROCEDURE_ID, self.TOKEN)

        # Then
        assert sorted(application_ids) == [1, 2, 3, 4, 5]

    def test_returns_applications_with_chosen_states(self, get_all_applications_for_procedure):
        # Given
        get_all_applications_for_procedure.return_value = {
            "dossiers": [
                {"id": 1, "updated_at": "2019-02-04T16:51:18.293Z", "state": "closed"},
                {"id": 2, "updated_at": "2019-02-04T16:51:18.293Z", "state": "initiated"},
                {"id": 3, "updated_at": "2019-02-03T16:51:18.293Z", "state": "refused"},
                {"id": 4, "updated_at": "2019-02-03T16:51:18.293Z", "state": "received"},
                {"id": 5, "updated_at": "2019-02-03T16:51:18.293Z", "state": "without_continuation"},
            ],
            "pagination": {"page": 1, "resultats_par_page": 100, "nombre_de_page": 1},
        }

        # When
        application_ids = get_all_application_ids_for_demarche_simplifiee(
            self.PROCEDURE_ID,
            self.TOKEN,
            accepted_states=[DmsApplicationStates.received, DmsApplicationStates.without_continuation],
        )

        # Then
        assert sorted(application_ids) == [4, 5]

    def test_returns_all_applications_if_no_date_specified(self, get_all_applications_for_procedure):
        # Given
        get_all_applications_for_procedure.return_value = {
            "dossiers": [
                {"id": 2, "updated_at": "2019-02-04T16:51:18.293Z", "state": "closed"},
                {"id": 3, "updated_at": "2018-12-17T16:51:18.293Z", "state": "closed"},
            ],
            "pagination": {"page": 1, "resultats_par_page": 100, "nombre_de_page": 1},
        }

        # When
        application_ids = get_all_application_ids_for_demarche_simplifiee(self.PROCEDURE_ID, self.TOKEN)

        # Then
        assert sorted(application_ids) == [2, 3]

    def test_returns_applications_updated_after_last_update_in_database_only(self, get_all_applications_for_procedure):
        # Given
        get_all_applications_for_procedure.return_value = {
            "dossiers": [
                {"id": 2, "updated_at": "2019-02-04T16:51:18.293Z", "state": "closed"},
                {"id": 3, "updated_at": "2018-12-17T16:51:18.293Z", "state": "closed"},
            ],
            "pagination": {"page": 1, "resultats_par_page": 100, "nombre_de_page": 1},
        }

        # When
        application_ids = get_all_application_ids_for_demarche_simplifiee(
            self.PROCEDURE_ID, self.TOKEN, datetime(2019, 1, 1)
        )

        # Then
        assert application_ids == [2]

    def test_returns_list_of_ids_ordered_by_updated_at_asc(self, get_all_applications_for_procedure):
        # Given
        get_all_applications_for_procedure.return_value = {
            "dossiers": [
                {"id": 1, "updated_at": "2019-02-04T16:51:18.293Z", "state": "closed"},
                {"id": 2, "updated_at": "2018-12-17T16:51:18.293Z", "state": "closed"},
                {"id": 3, "updated_at": "2018-11-17T16:51:18.293Z", "state": "closed"},
                {"id": 4, "updated_at": "2019-02-17T16:51:18.293Z", "state": "closed"},
            ],
            "pagination": {"page": 1, "resultats_par_page": 100, "nombre_de_page": 1},
        }

        # When
        application_ids = get_all_application_ids_for_demarche_simplifiee(self.PROCEDURE_ID, self.TOKEN)

        # Then
        assert application_ids == [3, 2, 1, 4]


@patch("pcapi.connectors.api_demarches_simplifiees.get_all_applications_for_procedure")
@patch("pcapi.domain.demarches_simplifiees.get_already_processed_applications_ids")
class GetClosedApplicationIdsForBeneficiaryImportTest:
    def setup_method(self):
        self.PROCEDURE_ID = "123456789"
        self.TOKEN = "AZERTY123/@.,!é"

    def test_returns_applications_with_state_closed_only(
        self, get_already_processed_applications_ids, get_all_applications_for_procedure
    ):
        # Given
        get_all_applications_for_procedure.return_value = {
            "dossiers": [
                {"id": 2, "updated_at": "2019-02-04T16:51:18.293Z", "state": "closed"},
                {"id": 3, "updated_at": "2019-02-03T16:51:18.293Z", "state": "initiated"},
            ],
            "pagination": {"page": 1, "resultats_par_page": 100, "nombre_de_page": 1},
        }
        get_already_processed_applications_ids.return_value = set()

        # When
        application_ids = get_closed_application_ids_for_demarche_simplifiee(self.PROCEDURE_ID, self.TOKEN)

        # Then
        assert application_ids == [2]


@patch("pcapi.connectors.api_demarches_simplifiees.get_application_details")
class GetOffererBankInformation_applicationDetailsByApplicationIdTest:
    def test_retrieve_and_format_all_fields(self, get_application_details):
        # Given
        updated_at = datetime(2020, 1, 3)
        get_application_details.return_value = offerer_demarche_simplifiee_application_detail_response(
            siren="123456789",
            bic="SOGEFRPP",
            iban="FR7630007000111234567890144",
            idx=8,
            state="closed",
            updated_at=updated_at.strftime(DATE_ISO_FORMAT),
        )

        # When
        application_details = get_offerer_bank_information_application_details_by_application_id(8)

        # Then
        assert isinstance(application_details, ApplicationDetail)
        assert application_details.siren == "123456789"
        assert application_details.status == BankInformationStatus.ACCEPTED
        assert application_details.application_id == 8
        assert application_details.iban == "FR7630007000111234567890144"
        assert application_details.bic == "SOGEFRPP"
        assert application_details.siret == None
        assert application_details.venue_name == None
        assert application_details.modification_date == updated_at

    @patch("pcapi.domain.demarches_simplifiees.format_raw_iban_and_bic")
    def test_format_bic_and_iban(self, mock_format_raw_iban_and_bic, get_application_details):
        # Given
        updated_at = datetime(2020, 1, 3)
        get_application_details.return_value = offerer_demarche_simplifiee_application_detail_response(
            siren="123456789",
            bic="SOGeferp",
            iban="F R763000 700011123 45 67890144",
            idx=8,
            state="closed",
            updated_at=updated_at.strftime(DATE_ISO_FORMAT),
        )

        # When
        get_offerer_bank_information_application_details_by_application_id(8)

        # Then
        mock_format_raw_iban_and_bic.assert_has_calls([call("F R763000 700011123 45 67890144"), call("SOGeferp")])


@patch("pcapi.connectors.api_demarches_simplifiees.get_application_details")
class GetVenueBankInformation_applicationDetailsByApplicationIdTest:
    def test_retrieve_and_format_all_fields_when_with_siret(self, get_application_details):
        # Given
        updated_at = datetime(2020, 1, 3)
        get_application_details.return_value = venue_demarche_simplifiee_application_detail_response_with_siret(
            siret="12345678900012",
            siren="123456789",
            bic="SOGEFRPP",
            iban="FR7630007000111234567890144",
            idx=8,
            state="closed",
            updated_at=updated_at.strftime(DATE_ISO_FORMAT),
        )

        # When
        application_details = get_venue_bank_information_application_details_by_application_id(8)

        # Then
        assert isinstance(application_details, ApplicationDetail)
        assert application_details.siren == "123456789"
        assert application_details.status == BankInformationStatus.ACCEPTED
        assert application_details.application_id == 8
        assert application_details.iban == "FR7630007000111234567890144"
        assert application_details.bic == "SOGEFRPP"
        assert application_details.siret == "12345678900012"
        assert application_details.venue_name == None
        assert application_details.modification_date == updated_at

    def test_retrieve_and_format_all_fields_when_without_siret(self, get_application_details):
        # Given
        updated_at = datetime(2020, 1, 3)
        get_application_details.return_value = venue_demarche_simplifiee_application_detail_response_without_siret(
            siret="12345678900012",
            bic="SOGEFRPP",
            iban="FR7630007000111234567890144",
            idx=8,
            state="closed",
            updated_at=updated_at.strftime(DATE_ISO_FORMAT),
        )

        # When
        application_details = get_venue_bank_information_application_details_by_application_id(8)

        # Then
        assert isinstance(application_details, ApplicationDetail)
        assert application_details.siren == "123456789"
        assert application_details.status == BankInformationStatus.ACCEPTED
        assert application_details.application_id == 8
        assert application_details.iban == "FR7630007000111234567890144"
        assert application_details.bic == "SOGEFRPP"
        assert application_details.siret == ""
        assert application_details.venue_name == "VENUE_NAME"
        assert application_details.modification_date == updated_at

    @patch("pcapi.domain.demarches_simplifiees.format_raw_iban_and_bic")
    def test_format_bic_and_iban_when_with_siret(self, mock_format_raw_iban_and_bic, get_application_details):
        # Given
        updated_at = datetime(2020, 1, 3)
        get_application_details.return_value = venue_demarche_simplifiee_application_detail_response_with_siret(
            siret="12345678912345",
            bic="SOGeferp",
            iban="F R763000 700011123 45 67890144",
            idx=8,
            state="closed",
            updated_at=updated_at.strftime(DATE_ISO_FORMAT),
        )

        # When
        get_offerer_bank_information_application_details_by_application_id(8)

        # Then
        mock_format_raw_iban_and_bic.assert_has_calls([call("F R763000 700011123 45 67890144"), call("SOGeferp")])

    @patch("pcapi.domain.demarches_simplifiees.format_raw_iban_and_bic")
    def test_format_bic_and_iban_when_without_siret(self, mock_format_raw_iban_and_bic, get_application_details):
        # Given
        updated_at = datetime(2020, 1, 3)
        get_application_details.return_value = venue_demarche_simplifiee_application_detail_response_without_siret(
            siret="12345678912345",
            bic="SOGeferp",
            iban="F R763000 700011123 45 67890144",
            idx=8,
            state="closed",
            updated_at=updated_at.strftime(DATE_ISO_FORMAT),
        )

        # When
        get_offerer_bank_information_application_details_by_application_id(8)

        # Then
        mock_format_raw_iban_and_bic.assert_has_calls([call("F R763000 700011123 45 67890144"), call("SOGeferp")])


class GetStatusFromDemarchesSimplifieesApplicationStateTest:
    def test_correctly_infer_status_from_state(self):
        # Given
        states = ["closed", "initiated", "refused", "received", "without_continuation"]

        # when
        statuses = [_get_status_from_demarches_simplifiees_application_state(state) for state in states]

        # Then
        assert statuses == [
            BankInformationStatus.ACCEPTED,
            BankInformationStatus.DRAFT,
            BankInformationStatus.REJECTED,
            BankInformationStatus.DRAFT,
            BankInformationStatus.REJECTED,
        ]

    def test_raise_error_in_unknown_state(self):
        # Given
        state = "wrong"

        # When
        with pytest.raises(CannotRegisterBankInformation) as error:
            _get_status_from_demarches_simplifiees_application_state(state)

        # Then
        assert error.value.args == (f"Unknown Demarches Simplifiées state {state}",)


class ParseRawBicDataTest:
    def test_parsing_works(self):
        INPUT_DATA = {
            "dossier": {
                "champs": [
                    {"id": "Q2hhbXAtNDA3ODk1", "label": "Mes informations", "stringValue": "", "value": None},
                    {"id": "Q2hhbXAtNDA3ODg5", "label": "Mon prénom", "stringValue": "John", "value": "John"},
                    {"id": "Q2hhbXAtNDA3ODkw", "label": "Mon nom", "stringValue": "Doe", "value": "Doe"},
                    {
                        "id": "Q2hhbXAtNDA3ODky",
                        "label": "Mon numéro de téléphone",
                        "stringValue": "01 02 03 04 05",
                        "value": "0102030405",
                    },
                    {
                        "id": "Q2hhbXAtODU2NzEz",
                        "label": "Informations relatives au responsable légal "
                        "et à ma délégation de gestion financière",
                        "stringValue": "",
                        "value": None,
                    },
                    {
                        "file": {
                            "checksum": "dIUGYwKmurZztL/3bL/m/g==",
                            "contentType": "application/pdf",
                            "filename": "test.pdf",
                            "url": "http://localhost/somefile",
                        },
                        "id": "Q2hhbXAtMzUyNzI1",
                        "label": "Responsable légal de votre structure ou de " "votre lieu",
                        "stringValue": "",
                    },
                    {
                        "file": {
                            "checksum": "dIUGYwKmurZztL/3bL/m/g==",
                            "contentType": "application/pdf",
                            "filename": "test.pdf",
                            "url": "http://https://localhost/somefile",
                        },
                        "id": "Q2hhbXAtMjA2MTE4Nw==",
                        "label": "Document d'identité de ce dirigeant (daté, " "certifié conforme et signé)",
                        "stringValue": "",
                    },
                    {
                        "file": None,
                        "id": "Q2hhbXAtNzAwNTUy",
                        "label": "Si vous n'êtes pas le responsable légal " "de votre structure ou de votre lieu",
                        "stringValue": "",
                    },
                    {
                        "id": "Q2hhbXAtMzUyNzIz",
                        "label": "Informations sur le lieu à rembourser",
                        "stringValue": "",
                        "value": None,
                    },
                    {
                        "etablissement": {
                            "address": {
                                "cityCode": "75108",
                                "cityName": "PARIS 8",
                                "departmentCode": None,
                                "departmentName": None,
                                "geometry": None,
                                "label": "GAUMONT "
                                "ALESIA\r\n"
                                "2 RUE "
                                "LAMENNAIS\r\n"
                                "75008 PARIS "
                                "8\r\n"
                                "FRANCE",
                                "postalCode": "75008",
                                "regionCode": None,
                                "regionName": None,
                                "streetAddress": "2 RUE " "LAMENNAIS",
                                "streetName": "LAMENNAIS",
                                "streetNumber": "2",
                                "type": "housenumber",
                            },
                            "association": None,
                            "entreprise": {
                                "capitalSocial": "38130",
                                "codeEffectifEntreprise": "12",
                                "dateCreation": "2001-06-27",
                                "formeJuridique": "SAS, " "société " "par " "actions " "simplifiée",
                                "formeJuridiqueCode": "5710",
                                "inlineAdresse": "2 " "RUE " "LAMENNAIS, " "75008 " "PARIS " "8",
                                "nom": None,
                                "nomCommercial": "",
                                "numeroTvaIntracommunautaire": "FR67438391195",
                                "prenom": None,
                                "raisonSociale": "GAUMONT " "ALESIA",
                                "siren": "438391195",
                                "siretSiegeSocial": "43839119500056",
                            },
                            "libelleNaf": "Projection de films " "cinématographiques",
                            "naf": "5914Z",
                            "siegeSocial": True,
                            "siret": "43839119500056",
                        },
                        "id": "Q2hhbXAtNzgyODAw",
                        "label": "SIRET",
                        "stringValue": "43839119500056",
                    },
                    {"id": "Q2hhbXAtNzAwNTA5", "label": "Vos coordonnées bancaires", "stringValue": "", "value": None},
                    {
                        "id": "Q2hhbXAtMzUyNzIy",
                        "label": "IBAN",
                        "stringValue": "FR7630001007941234567890185",
                        "value": "FR7630001007941234567890185",
                    },
                    {"id": "Q2hhbXAtMzUyNzI3", "label": "BIC", "stringValue": "QSDFGH8Z", "value": "QSDFGH8Z"},
                    {
                        "file": {
                            "checksum": "dIUGYwKmurZztL/3bL/m/g==",
                            "contentType": "application/pdf",
                            "filename": "test.pdf",
                            "url": "http://localhost/somefile",
                        },
                        "id": "Q2hhbXAtODU2ODE4",
                        "label": "RIB",
                        "stringValue": "",
                    },
                ],
                "dateDerniereModification": "2021-11-12T14:51:42+01:00",
                "state": "en_construction",
            }
        }
        result = parse_raw_bic_data(INPUT_DATA)
        assert result == {
            "status": "en_construction",
            "updated_at": "2021-11-12T14:51:42+01:00",
            "firstname": "John",
            "lastname": "Doe",
            "phone_number": "0102030405",
            "siret": "43839119500056",
            "siren": "438391195",
            "iban": "FR7630001007941234567890185",
            "bic": "QSDFGH8Z",
        }
