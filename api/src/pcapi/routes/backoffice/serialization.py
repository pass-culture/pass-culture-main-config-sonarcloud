import datetime
import typing

import pydantic

from pcapi.core.fraud import models as fraud_models
import pcapi.core.offerers.models as offerers_models
from pcapi.core.subscription import models as subscription_models
from pcapi.core.subscription.phone_validation import exceptions as phone_validation_exceptions
from pcapi.core.users import models as users_models
from pcapi.routes.serialization import BaseModel
from pcapi.utils import phone_number as phone_number_utils
from pcapi.utils.email import sanitize_email


class Permission(BaseModel):
    class Config:
        orm_mode = True

    id: int
    name: str
    category: str | None


class Role(BaseModel):
    class Config:
        orm_mode = True

    id: int
    name: str
    permissions: list[Permission]


class ListRoleResponseModel(BaseModel):
    class Config:
        orm_mode = True

    roles: list[Role]


class ListPermissionResponseModel(BaseModel):
    class Config:
        orm_mode = True

    permissions: list[Permission]


class RoleRequestModel(BaseModel):
    name: str = pydantic.Field(..., min_length=1)
    permissionIds: list[int]


class PublicAccount(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True

    id: int
    firstName: str | None
    lastName: str | None
    dateOfBirth: datetime.datetime | None
    email: str
    phoneNumber: str | None
    roles: list[users_models.UserRole]
    isActive: bool
    address: str | None
    postalCode: str | None
    city: str | None


class PaginableQuery(BaseModel):
    page: int | None = 1
    perPage: int | None = 20
    sort: str | None = None


class SearchQuery(PaginableQuery):
    q: str


class PaginatedResponse(BaseModel):
    pages: int
    total: int
    page: int
    size: int
    sort: str | None
    data: typing.Any


class ListPublicAccountsResponseModel(PaginatedResponse):
    data: list[PublicAccount]


class PublicAccountUpdateRequest(BaseModel):
    firstName: str | None
    lastName: str | None
    dateOfBirth: datetime.datetime | None
    idPieceNumber: str | None
    email: pydantic.EmailStr | None
    phoneNumber: str | None
    address: str | None
    postalCode: str | None
    city: str | None

    @pydantic.validator("email", pre=True)
    def validate_email(cls, email: str) -> str:  # pylint: disable=no-self-argument
        if not email:
            return email
        return sanitize_email(email)

    @pydantic.validator("phoneNumber")
    def validate_phone_number(cls, phone_number: str) -> str:  # pylint: disable=no-self-argument
        if not phone_number:
            return phone_number

        try:
            # Convert to international format
            return phone_number_utils.ParsedPhoneNumber(phone_number).phone_number
        except phone_validation_exceptions.InvalidPhoneNumber:
            raise ValueError(f"Format de num??ro de t??l??phone invalide : {phone_number}")


class GetBeneficiaryCreditResponseModel(BaseModel):
    initialCredit: float
    remainingCredit: float
    remainingDigitalCredit: float
    dateCreated: datetime.datetime | None


class AuthTokenQuery(BaseModel):
    token: str


class AuthTokenResponseModel(BaseModel):
    token: str


class SubscriptionItemModel(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True

    type: subscription_models.SubscriptionStep
    status: subscription_models.SubscriptionItemStatus


class IdCheckItemModel(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True

    @classmethod
    def from_orm(cls: typing.Any, fraud_check: fraud_models.BeneficiaryFraudCheck):  # type: ignore
        fraud_check.technicalDetails = fraud_check.resultContent

        if fraud_check.type == fraud_models.FraudCheckType.DMS and fraud_check.resultContent is not None:
            dms_content = fraud_models.DMSContent(**fraud_check.resultContent)  # type: ignore [arg-type]
            fraud_check.sourceId = str(dms_content.procedure_number)

        return super().from_orm(fraud_check)

    type: fraud_models.FraudCheckType
    dateCreated: datetime.datetime
    thirdPartyId: str
    status: fraud_models.FraudCheckStatus | None
    reason: str | None
    reasonCodes: list[fraud_models.FraudReasonCode] | None
    technicalDetails: dict | None
    sourceId: str | None = None  # DMS only


class EligibilitySubscriptionHistoryModel(BaseModel):
    subscriptionItems: list[SubscriptionItemModel]
    idCheckHistory: list[IdCheckItemModel]


class GetUserSubscriptionHistoryResponseModel(BaseModel):
    subscriptions: dict[str, EligibilitySubscriptionHistoryModel]


class BeneficiaryReviewRequestModel(BaseModel):
    class Config:
        extra = pydantic.Extra.forbid

    reason: str
    review: fraud_models.FraudReviewStatus
    eligibility: str | None


class BeneficiaryReviewResponseModel(BeneficiaryReviewRequestModel):
    userId: int
    authorId: int


class PublicHistoryItem(BaseModel):
    class config:
        extra = pydantic.Extra.forbid

    action: str
    datetime: datetime.datetime
    message: str


class PublicHistoryResponseModel(BaseModel):
    history: list[PublicHistoryItem]


class ProSearchQuery(PaginableQuery):
    q: str
    type: str  # "proUser" or "venue" or "offerer"


class ProResultPayload(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True


class ProUserPayload(ProResultPayload):
    firstName: str | None
    lastName: str | None
    email: str
    phoneNumber: str | None


class OffererPayload(ProResultPayload):
    name: str | None
    siren: str | None


class VenuePayload(ProResultPayload):
    name: str | None
    email: str | None
    siret: str | None
    permanent: bool

    @classmethod
    def from_orm(cls: typing.Type["VenuePayload"], venue: offerers_models.Venue) -> "VenuePayload":
        if venue.contact and venue.contact.email:
            venue.email = venue.contact.email
        else:
            venue.email = venue.bookingEmail
        venue.permanent = venue.isPermanent
        return super().from_orm(venue)


class ProResult(BaseModel):
    resourceType: str  # "proUser" or "venue" or "offerer"
    id: int
    payload: ProResultPayload


class SearchProResponseModel(PaginatedResponse):
    data: list[ProResult]


class OffererAttachedUser(BaseModel):
    class Config:
        orm_mode = True

    id: int
    firstName: str | None
    lastName: str | None
    email: str


class OffererAttachedUsersResponseModel(BaseModel):
    data: list[OffererAttachedUser]
