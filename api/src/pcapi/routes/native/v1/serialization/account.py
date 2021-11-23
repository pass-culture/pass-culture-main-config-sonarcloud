import datetime
from enum import Enum
import re
from typing import Any
from typing import Optional
from uuid import UUID

from dateutil.relativedelta import relativedelta
import flask
import pydantic
from pydantic.class_validators import root_validator
from pydantic.class_validators import validator
from pydantic.fields import Field
from sqlalchemy.orm import joinedload

from pcapi.connectors.user_profiling import AgentType
from pcapi.core.bookings.models import Booking
from pcapi.core.bookings.models import BookingStatus
from pcapi.core.bookings.models import IndividualBooking
from pcapi.core.offers import validation
from pcapi.core.offers.models import Offer
from pcapi.core.offers.models import Stock
from pcapi.core.payments.models import DepositType
from pcapi.core.subscription import api as subscription_api
from pcapi.core.subscription import models as subscription_models
from pcapi.core.users import constants as users_constants
from pcapi.core.users.api import BeneficiaryValidationStep
from pcapi.core.users.api import get_domains_credit
from pcapi.core.users.api import get_next_beneficiary_validation_step
from pcapi.core.users.models import EligibilityCheckMethods
from pcapi.core.users.models import EligibilityType
from pcapi.core.users.models import ExpenseDomain
from pcapi.core.users.models import User
from pcapi.core.users.models import UserRole
from pcapi.core.users.models import VOID_FIRST_NAME
from pcapi.core.users.models import VOID_PUBLIC_NAME
from pcapi.core.users.models import get_age_from_birth_date
from pcapi.core.users.models import get_eligibility
from pcapi.models.feature import FeatureToggle
from pcapi.routes.native.utils import convert_to_cent
from pcapi.serialization.utils import to_camel
from pcapi.utils.date import format_into_utc_date

from . import BaseModel


class ActivityEnum(str, Enum):
    middle_school_student = "Collégien"
    high_school_student = "Lycéen"
    student = "Étudiant"
    employee = "Employé"
    apprentice = "Apprenti"
    apprentice_student = "Alternant"
    volunteer = "Volontaire"
    inactive = "Inactif"
    unemployed = "Chômeur"


class AccountRequest(BaseModel):
    email: str
    password: str
    birthdate: datetime.date
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    marketing_email_subscription: Optional[bool] = False
    token: str
    postal_code: Optional[str] = None
    apps_flyer_user_id: Optional[str] = None
    apps_flyer_platform: Optional[str] = None

    class Config:
        alias_generator = to_camel

    @validator("first_name", "last_name", always=True)
    def first_and_last_name_mandatory(  # pylint: disable=no-self-argument
        cls, name: Optional[str], values: dict[str, Any]
    ) -> str:
        if FeatureToggle.ENABLE_UBBLE.is_active() and get_eligibility(get_age_from_birth_date(values["birthdate"])):
            if not name or name.isspace():
                raise ValueError("Le prénom et le nom sont obligatoires pour tout jeune éligible")
            name = name.strip()
        return name


class InstitutionalProjectRedactorAccountRequest(BaseModel):
    email: str
    password: str

    class Config:
        alias_generator = to_camel


class CulturalSurveyRequest(BaseModel):
    needs_to_fill_cultural_survey: bool
    cultural_survey_id: Optional[UUID]

    class Config:
        alias_generator = to_camel


class Expense(BaseModel):
    domain: ExpenseDomain
    current: int
    limit: int

    _convert_current = validator("current", pre=True, allow_reuse=True)(convert_to_cent)
    _convert_limit = validator("limit", pre=True, allow_reuse=True)(convert_to_cent)

    class Config:
        orm_mode = True


class NotificationSubscriptions(BaseModel):
    marketing_email: bool
    marketing_push: bool

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        orm_mode = True


class Credit(BaseModel):
    initial: int
    remaining: int

    _convert_initial = validator("initial", pre=True, allow_reuse=True)(convert_to_cent)
    _convert_remaining = validator("remaining", pre=True, allow_reuse=True)(convert_to_cent)

    class Config:
        orm_mode = True


class DomainsCredit(BaseModel):
    all: Credit
    digital: Optional[Credit]
    physical: Optional[Credit]

    class Config:
        orm_mode = True


class CallToActionMessage(BaseModel):
    callToActionTitle: Optional[str]
    callToActionLink: Optional[str]
    callToActionIcon: Optional[subscription_models.CallToActionIcon]

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        use_enum_values = True


class SubscriptionMessage(BaseModel):
    userMessage: str
    callToAction: Optional[CallToActionMessage]
    popOverIcon: Optional[subscription_models.PopOverIcon]
    updatedAt: datetime.datetime

    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        json_encoders = {datetime.datetime: format_into_utc_date}
        use_enum_values = True

    @classmethod
    def from_model(
        cls, model_instance: Optional[subscription_models.SubscriptionMessage]
    ) -> Optional["SubscriptionMessage"]:
        if not model_instance:
            return None
        cta_message = None
        if any((model_instance.callToActionTitle, model_instance.callToActionLink, model_instance.callToActionIcon)):
            cta_message = CallToActionMessage(
                callToActionTitle=model_instance.callToActionTitle,
                callToActionLink=model_instance.callToActionLink,
                callToActionIcon=model_instance.callToActionIcon,
            )
        subscription_message = SubscriptionMessage(
            userMessage=model_instance.userMessage,
            callToAction=cta_message,
            popOverIcon=model_instance.popOverIcon,
            updatedAt=model_instance.dateCreated,
        )
        return subscription_message


class UserProfileResponse(BaseModel):
    allowed_eligibility_check_methods: Optional[list[EligibilityCheckMethods]]
    booked_offers: dict[str, int]
    dateOfBirth: Optional[datetime.date]
    deposit_expiration_date: Optional[datetime.datetime]
    deposit_type: Optional[DepositType]
    deposit_version: Optional[int]
    domains_credit: Optional[DomainsCredit]
    eligibility: Optional[EligibilityType]
    eligibility_end_datetime: Optional[datetime.datetime]
    eligibility_start_datetime: Optional[datetime.datetime]
    email: str
    firstName: Optional[str]
    hasCompletedIdCheck: Optional[bool]
    id: int
    isBeneficiary: bool
    isEligibleForBeneficiaryUpgrade: bool
    lastName: Optional[str]
    needsToFillCulturalSurvey: bool
    next_beneficiary_validation_step: Optional[BeneficiaryValidationStep]
    phoneNumber: Optional[str]
    publicName: Optional[str] = Field(None, alias="pseudo")
    recreditAmountToShow: Optional[int]
    roles: list[UserRole]
    show_eligible_card: bool
    subscriptions: NotificationSubscriptions  # if we send user.notification_subscriptions, pydantic will take the column and not the property
    subscriptionMessage: Optional[SubscriptionMessage]

    _convert_recredit_amount_to_show = validator("recreditAmountToShow", pre=True, allow_reuse=True)(convert_to_cent)

    class Config:
        orm_mode = True
        alias_generator = to_camel
        allow_population_by_field_name = True
        json_encoders = {datetime.datetime: format_into_utc_date}
        use_enum_values = True

    @validator("publicName", pre=True)
    def format_public_name(cls, publicName: str) -> Optional[str]:  # pylint: disable=no-self-argument
        return publicName if publicName != VOID_PUBLIC_NAME else None

    @validator("firstName", pre=True)
    def format_first_name(cls, firstName: Optional[str]) -> Optional[str]:  # pylint: disable=no-self-argument
        return firstName if firstName != VOID_FIRST_NAME else None

    @staticmethod
    def _show_eligible_card(user: User) -> bool:
        return (
            relativedelta(user.dateCreated, user.dateOfBirth).years < users_constants.ELIGIBILITY_AGE_18
            and user.has_beneficiary_role is False
            and user.eligibility == EligibilityType.AGE18
        )

    @staticmethod
    def _get_booked_offers(user: User) -> dict:
        not_cancelled_bookings = (
            Booking.query.join(Booking.individualBooking)
            .options(joinedload(Booking.stock).joinedload(Stock.offer).load_only(Offer.id))
            .filter(
                IndividualBooking.userId == user.id,
                Booking.status != BookingStatus.CANCELLED,
                Booking.isCancelled.is_(False),
            )
        )

        return {booking.stock.offer.id: booking.id for booking in not_cancelled_bookings}

    @classmethod
    def from_orm(cls, user: User):  # type: ignore
        user.show_eligible_card = cls._show_eligible_card(user)
        user.subscriptions = user.get_notification_subscriptions()
        user.domains_credit = get_domains_credit(user)
        user.booked_offers = cls._get_booked_offers(user)
        user.next_beneficiary_validation_step = get_next_beneficiary_validation_step(user)
        user.isEligibleForBeneficiaryUpgrade = user.is_eligible_for_beneficiary_upgrade()
        result = super().from_orm(user)
        result.subscriptionMessage = SubscriptionMessage.from_model(
            subscription_api.get_latest_subscription_message(user)
        )
        # FIXME: (Lixxday) Remove after isBeneficiary column has been deleted
        result.isBeneficiary = user.is_beneficiary
        return result


class UserProfileUpdateRequest(BaseModel):
    subscriptions: Optional[NotificationSubscriptions]


class UserProfileEmailUpdate(BaseModel):
    email: pydantic.EmailStr
    password: pydantic.constr(strip_whitespace=True, min_length=8, strict=True)  # type: ignore


class ValidateEmailRequest(BaseModel):
    token: str


class BeneficiaryInformationUpdateRequest(BaseModel):
    activity: ActivityEnum
    address: Optional[str]
    city: str
    phone: Optional[str]
    postal_code: str

    class Config:
        use_enum_values = True
        alias_generator = to_camel


class ResendEmailValidationRequest(BaseModel):
    email: str


class GetIdCheckTokenResponse(BaseModel):
    token: Optional[str]
    token_timestamp: Optional[datetime.datetime]


class ValidatePhoneNumberRequest(BaseModel):
    code: str


class SendPhoneValidationRequest(BaseModel):
    phoneNumber: Optional[str]


class UploadIdentityDocumentRequest(BaseModel):
    token: str

    def get_image_as_bytes(self, request: flask.Request) -> bytes:
        """
        Get the image from the POSTed data (request) or from the form field
        (in which case it's supposed to be an URL that we are going to request.
        Only the max size is checked at this stage, and possibly the content type header
        """
        if "identityDocumentFile" in request.files:
            blob = request.files["identityDocumentFile"]
            image_as_bytes = blob.read()
            return validation.get_uploaded_image(image_as_bytes, 10 * 1000 * 1000)

        raise validation.exceptions.MissingImage


class UserProfilingFraudRequest(BaseModel):
    # Moving from session_id to sessionId - remove session_id and set sessionId not Optional when app version is forced
    # to a new minimal version. Also restore a simple validator session_id_alphanumerics for sessionId
    session_id: Optional[str]
    sessionId: Optional[str]
    agentType: Optional[AgentType]

    @root_validator()
    def session_id_alphanumerics(cls, values: dict[str, Any]) -> dict[str, Any]:  # pylint: disable=no-self-argument
        session_id = values.get("sessionId") or values.get("session_id")
        if not session_id:
            raise ValueError("L'identifiant de session est manquant")
        if not re.match(r"^[A-Za-z0-9_-]{1,128}$", session_id):
            raise ValueError(
                "L'identifiant de session ne doit être composé exclusivement que de caratères alphanumériques"
            )
        values["sessionId"] = session_id
        return values

    @validator("agentType", always=True)
    def agent_type_validation(cls, agent_type: str) -> str:  # pylint: disable=no-self-argument
        if agent_type is None:
            agent_type = AgentType.AGENT_MOBILE
        if agent_type not in (AgentType.BROWSER_COMPUTER, AgentType.BROWSER_MOBILE, AgentType.AGENT_MOBILE):
            raise ValueError("agentType est invalide")
        return agent_type


class UserProfilingSessionIdResponse(BaseModel):
    sessionId: str


class IdentificationSessionRequest(BaseModel):
    redirectUrl: str


class IdentificationSessionResponse(BaseModel):
    identificationUrl: str
