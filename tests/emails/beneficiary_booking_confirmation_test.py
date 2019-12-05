from datetime import datetime, timezone
from unittest.mock import patch

from emails.beneficiary_booking_confirmation import retrieve_data_for_user_booking_confirmation_email
from models import PcObject
from tests.conftest import clean_database
from tests.test_utils import create_offerer, create_venue, create_user, create_booking, create_offer_with_event_product, \
    create_stock_from_offer, create_deposit, create_offer_with_thing_product, create_mediation


@clean_database
def test_should_return_event_specific_data_for_email_when_offer_is_an_event(app):
    # Given
    user = create_user(first_name='Joe', email='joe@example.com')
    deposit = create_deposit(user)
    offerer = create_offerer(idx=1, name='Théâtre du coin')
    venue = create_venue(offerer, 'Lieu de l\'offreur', idx=1,
                         address='25 avenue du lieu')
    event_offer = create_offer_with_event_product(venue, event_name='Super événement', idx=34)
    mediation = create_mediation(event_offer, idx=22)
    beginning_datetime = datetime(2019, 11, 6, 14, 59, 5, tzinfo=timezone.utc)
    stock = create_stock_from_offer(event_offer, beginning_datetime=beginning_datetime, price=23, available=10)
    booking_datetime = datetime(2019, 10, 3, 13, 24, 6, tzinfo=timezone.utc)
    booking = create_booking(user, stock, venue, token='ABC123', date_created=booking_datetime)
    recipient = [user.email]
    stock.bookings = [booking]

    PcObject.save(mediation)
    PcObject.save(deposit)
    PcObject.save(stock)

    # When
    email_data = retrieve_data_for_user_booking_confirmation_email(booking, recipient)

    # Then
    assert email_data == {
        'FromEmail': 'support@passculture.app',
        'MJ-TemplateID': 1089755,
        'MJ-TemplateLanguage': True,
        'To': 'dev@passculture.app',
        'Vars':
            {
                'user_first_name': 'Joe',
                'booking_date': '3 octobre',
                'booking_hour': '15h24',
                'offer_name': 'Super événement',
                'offerer_name': 'Théâtre du coin',
                'event_date': '6 novembre',
                'event_hour': '15h59',
                'offer_price': 23,
                'offer_token': 'ABC123',
                'venue_name': 'Lieu de l\'offreur',
                'venue_address': '25 avenue du lieu',
                'all_but_not_virtual_thing': 1,
                'all_things_not_virtual_thing': 0,
                'is_event': 1,
                'offer_id': 34,
                'mediation_id': 22,
                'env': '-development'
            }
    }


@clean_database
def test_should_return_thing_specific_data_for_email_when_offer_is_a_thing(app):
    # Given
    user = create_user(first_name='Joe', email='joe@example.com')
    deposit = create_deposit(user)
    offerer = create_offerer(idx=1, name='Théâtre de l\'angle')
    venue = create_venue(offerer, 'Lieu', idx=1,
                         address='22 avenue du lieu')
    thing_offer = create_offer_with_thing_product(venue, thing_name='Super bien culturel', idx=33)
    mediation = create_mediation(thing_offer, idx=24)
    stock = create_stock_from_offer(thing_offer, price=15, available=10)
    booking_datetime = datetime(2019, 10, 3, 13, 24, 6, tzinfo=timezone.utc)
    booking = create_booking(user, stock, venue, token='123ABC', date_created=booking_datetime)
    recipient = [user.email]
    stock.bookings = [booking]

    PcObject.save(mediation)
    PcObject.save(deposit)
    PcObject.save(stock)

    # When
    email_data = retrieve_data_for_user_booking_confirmation_email(booking, recipient)

    # Then
    assert email_data == {
        'FromEmail': 'support@passculture.app',
        'MJ-TemplateID': 1089755,
        'MJ-TemplateLanguage': True,
        'To': 'dev@passculture.app',
        'Vars':
            {
                'user_first_name': 'Joe',
                'booking_date': '3 octobre',
                'booking_hour': '15h24',
                'offer_name': 'Super bien culturel',
                'offerer_name': 'Théâtre de l\'angle',
                'event_date': '',
                'event_hour': '',
                'offer_price': 15,
                'offer_token': '123ABC',
                'venue_name': 'Lieu',
                'venue_address': '22 avenue du lieu',
                'all_but_not_virtual_thing': 1,
                'all_things_not_virtual_thing': 1,
                'is_event': 0,
                'offer_id': 33,
                'mediation_id': 24,
                'env': '-development'
            }
    }


@clean_database
def test_should_return_digital_thing_specific_data_for_email_when_offer_is_a_digital_thing(app):
    # Given
    user = create_user(first_name='Joe', email='joe@example.com')
    deposit = create_deposit(user)
    offerer = create_offerer(idx=1, name='Théâtre de l\'angle')
    venue = create_venue(offerer, 'Lieu', idx=1,
                         address='22 avenue du lieu')
    digital_thing_offer = create_offer_with_thing_product(venue, url='http://mon.url',
                                                          thing_name='Super offre numérique', idx=32)
    mediation = create_mediation(digital_thing_offer, idx=24)
    stock = create_stock_from_offer(digital_thing_offer, price=15, available=10)
    booking_datetime = datetime(2019, 10, 3, 13, 24, 6, tzinfo=timezone.utc)
    booking = create_booking(user, stock, venue, token='123ABC', date_created=booking_datetime)
    recipient = [user.email]
    stock.bookings = [booking]

    PcObject.save(mediation)
    PcObject.save(deposit)
    PcObject.save(stock)

    # When
    email_data = retrieve_data_for_user_booking_confirmation_email(booking, recipient)

    # Then
    assert email_data == {
        'FromEmail': 'support@passculture.app',
        'MJ-TemplateID': 1089755,
        'MJ-TemplateLanguage': True,
        'To': 'dev@passculture.app',
        'Vars':
            {
                'user_first_name': 'Joe',
                'booking_date': '3 octobre',
                'booking_hour': '15h24',
                'offer_name': 'Super offre numérique',
                'offerer_name': 'Théâtre de l\'angle',
                'event_date': '',
                'event_hour': '',
                'offer_price': 15,
                'offer_token': '123ABC',
                'venue_name': 'Lieu',
                'venue_address': '22 avenue du lieu',
                'all_but_not_virtual_thing': 0,
                'all_things_not_virtual_thing': 0,
                'is_event': 0,
                'offer_id': 32,
                'mediation_id': 24,
                'env': '-development'
            }
    }


@patch('utils.mailing.feature_send_mail_to_users_enabled', return_value=True)
@clean_database
def test_should_send_email_to_users_address_when_environment_is_production(app):
    # Given
    user = create_user(email='joe@example.com')
    offerer = create_offerer()
    venue = create_venue(offerer)
    event_offer = create_offer_with_event_product(venue)
    mediation = create_mediation(event_offer)
    stock = create_stock_from_offer(event_offer, price=0,
                                    beginning_datetime=datetime(2019, 10, 3, 13, 24, 6, tzinfo=timezone.utc))
    booking = create_booking(user, stock, venue)
    stock.bookings = [booking]
    PcObject.save(mediation)
    PcObject.save(stock)
    recipient = [user.email]

    # When
    email_data = retrieve_data_for_user_booking_confirmation_email(booking, recipient)

    # Then
    assert email_data.get('To') == 'joe@example.com'


@patch('emails.beneficiary_booking_confirmation.IS_PROD', True)
@clean_database
def test_should_not_set_env_variable_when_environment_is_production(app):
    # Given
    user = create_user()
    offerer = create_offerer()
    venue = create_venue(offerer)
    event_offer = create_offer_with_event_product(venue)
    mediation = create_mediation(event_offer)
    stock = create_stock_from_offer(event_offer, price=0,
                                    beginning_datetime=datetime(2019, 10, 3, 13, 24, 6, tzinfo=timezone.utc))
    booking = create_booking(user, stock, venue)
    stock.bookings = [booking]
    PcObject.save(mediation)
    PcObject.save(stock)
    recipient = [user.email]

    # When
    email_data = retrieve_data_for_user_booking_confirmation_email(booking, recipient)

    # Then
    assert email_data.get('Vars').get('env') == ''
