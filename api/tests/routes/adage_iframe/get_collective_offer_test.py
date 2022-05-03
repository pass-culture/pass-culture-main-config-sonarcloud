from datetime import datetime
from typing import ByteString

from freezegun.api import freeze_time
import pytest

from pcapi.core.educational import factories as educational_factories
from pcapi.core.educational.models import StudentLevels
from pcapi.core.testing import assert_num_queries

from tests.routes.adage_iframe.utils_create_test_token import create_adage_jwt_fake_valid_token


pytestmark = pytest.mark.usefixtures("db_session")

stock_date = datetime(2021, 5, 15)
educational_year_dates = {"start": datetime(2020, 9, 1), "end": datetime(2021, 8, 31)}


def _create_adage_valid_token_with_email(
    email: str,
    civility: str = "Mme",
    lastname: str = "LAPROF",
    firstname: str = "Jeanne",
    uai: str = "EAU123",
) -> ByteString:
    return create_adage_jwt_fake_valid_token(
        civility=civility, lastname=lastname, firstname=firstname, email=email, uai=uai
    )


@freeze_time("2020-11-17 15:00:00")
class Returns200Test:
    def test_get_collective_offer(self, client):
        # Given
        stock = educational_factories.CollectiveStockFactory(
            beginningDatetime=datetime(2021, 5, 15),
            collectiveOffer__name="offer name",
            collectiveOffer__description="offer description",
            price=10,
            collectiveOffer__students=[StudentLevels.GENERAL2],
        )

        adage_jwt_fake_valid_token = _create_adage_valid_token_with_email(email="toto@mail.com", uai="12890AI")
        client.auth_header = {"Authorization": f"Bearer {adage_jwt_fake_valid_token}"}
        offer_id = stock.collectiveOffer.id

        # When
        with assert_num_queries(1):
            response = client.get(f"/adage-iframe/collective/offers/{offer_id}")

        # Then
        assert response.status_code == 200
        assert response.json == {
            "description": "offer description",
            "id": offer_id,
            "isExpired": False,
            "isSoldOut": False,
            "name": "offer name",
            "stock": {
                "beginningDatetime": "2021-05-15T00:00:00Z",
                "bookingLimitDatetime": "2021-05-14T23:00:00Z",
                "id": stock.id,
                "isBookable": True,
                "price": 1000,
                "educationalPriceDetail": stock.priceDetail,
                "numberOfTickets": stock.numberOfTickets,
            },
            "subcategoryLabel": stock.collectiveOffer.subcategory.app_label,
            "venue": {
                "address": "1 boulevard Poissonnière",
                "city": "Paris",
                "coordinates": {"latitude": 48.87004, "longitude": 2.3785},
                "id": stock.collectiveOffer.venue.id,
                "name": stock.collectiveOffer.venue.name,
                "postalCode": "75000",
                "publicName": stock.collectiveOffer.venue.publicName,
                "managingOfferer": {"name": stock.collectiveOffer.venue.managingOfferer.name},
            },
            "audioDisabilityCompliant": False,
            "mentalDisabilityCompliant": False,
            "motorDisabilityCompliant": False,
            "visualDisabilityCompliant": False,
            "durationMinutes": None,
            "contactEmail": stock.collectiveOffer.contactEmail,
            "contactPhone": stock.collectiveOffer.contactPhone,
            "offerVenue": stock.collectiveOffer.offerVenue,
            "students": ["Lycée - Seconde"],
            "offerId": None,
            "educationalPriceDetail": stock.priceDetail,
        }


class Returns404Test:
    def test_should_return_404_when_no_collective_offer(self, client):
        # Given
        adage_jwt_fake_valid_token = _create_adage_valid_token_with_email(email="toto@mail.com", uai="12890AI")
        client.auth_header = {"Authorization": f"Bearer {adage_jwt_fake_valid_token}"}

        # When
        response = client.get("/adage-iframe/collective/offers/0")

        # Then
        assert response.status_code == 404