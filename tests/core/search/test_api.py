from unittest import mock

import pytest

from pcapi.core import search
import pcapi.core.offers.factories as offers_factories
import pcapi.core.search.testing as search_testing
from pcapi.core.testing import override_settings


pytestmark = pytest.mark.usefixtures("db_session")


def make_bookable_offer():
    return offers_factories.StockFactory().offer


def make_unbookable_offer():
    return offers_factories.OfferFactory()


def fail(*args, **kwargs):
    raise ValueError("It does not work")


def test_async_index_offer_ids(app):
    search.async_index_offer_ids({1, 2})
    assert set(app.redis_client.lrange("offer_ids", 0, 5)) == {b"1", b"2"}


def test_async_index_offers_of_venue_ids(app):
    search.async_index_offers_of_venue_ids({1, 2})
    assert set(app.redis_client.lrange("venue_ids_for_offers", 0, 5)) == {b"1", b"2"}


@override_settings(REDIS_VENUE_IDS_CHUNK_SIZE=1)
def test_index_offers_of_venues_in_queue(app):
    bookable_offer = make_bookable_offer()
    venue1 = bookable_offer.venue
    unbookable_offer = make_unbookable_offer()
    venue2 = unbookable_offer.venue
    app.redis_client.lpush("venue_ids_for_offers", venue1.id, venue2.id)

    # `index_offers_of_venues_in_queue` pops 1 venue from the queue
    # (REDIS_VENUE_IDS_FOR_OFFERS_TO_INDEX).
    search.index_offers_of_venues_in_queue()
    assert app.redis_client.lrange("venue_ids_for_offers", 0, 5) == [str(venue1.id).encode()]

    search.index_offers_of_venues_in_queue()
    assert app.redis_client.llen("venue_ids_for_offers") == 0

    assert bookable_offer.id in search_testing.search_store
    assert unbookable_offer.id not in search_testing.search_store


@override_settings(REDIS_VENUE_IDS_CHUNK_SIZE=1)
def test_index_venues_in_queue(app):
    venue1 = offers_factories.VenueFactory()
    venue2 = offers_factories.VenueFactory()
    app.redis_client.lpush("venue_ids_new", venue1.id, venue2.id)

    # `index_venues_in_queue` pops 1 venue from the queue (REDIS_VENUE_IDS_CHUNK_SIZE).
    search.index_venues_in_queue()
    assert app.redis_client.lrange("venue_ids_new", 0, 5) == [str(venue1.id).encode()]

    search.index_venues_in_queue()
    assert app.redis_client.llen("venue_ids_new") == 0


class ReindexOfferIdsTest:
    def test_index_new_offer(self):
        offer = make_bookable_offer()
        assert search_testing.search_store == {}
        search.reindex_offer_ids([offer.id])
        assert offer.id in search_testing.search_store

    def test_unindex_unbookable_offer(self, app):
        offer = make_unbookable_offer()
        app.redis_client.hset("indexed_offers", offer.id, "")
        search_testing.search_store[offer.id] = "dummy"
        search.reindex_offer_ids([offer.id])
        assert search_testing.search_store == {}

    def test_unindex_unbookable_offer_not_in_cache(self):
        offer = make_unbookable_offer()
        search_testing.search_store[offer.id] = "dummy"
        search.reindex_offer_ids([offer.id])
        assert offer.id in search_testing.search_store  # still there, not unindexed

    @mock.patch("pcapi.core.search.backends.testing.FakeClient.save_objects", fail)
    def test_handle_indexation_error(self):
        offer = make_bookable_offer()
        assert search_testing.search_store == {}
        with override_settings(IS_RUNNING_TESTS=False):  # as on prod: don't catch errors
            search.reindex_offer_ids([offer.id])
        assert offer.id not in search_testing.search_store
        backend = search._get_backends()[0]
        assert backend.pop_offer_ids_from_queue(5, from_error_queue=True) == {offer.id}

    @mock.patch("pcapi.core.search.backends.testing.FakeClient.delete_objects", fail)
    def test_handle_unindexation_error(self, app):
        offer = make_unbookable_offer()
        app.redis_client.hset("indexed_offers", offer.id, "")
        search_testing.search_store[offer.id] = "dummy"
        with override_settings(IS_RUNNING_TESTS=False):  # as on prod: don't catch errors
            search.reindex_offer_ids([offer.id])
        assert offer.id in search_testing.search_store
        backend = search._get_backends()[0]
        assert backend.pop_offer_ids_from_queue(5, from_error_queue=True) == {offer.id}


@override_settings(REDIS_OFFER_IDS_CHUNK_SIZE=3)
@mock.patch("pcapi.core.search._reindex_offer_ids")
class IndexOffersInQueueTest:
    def test_cron_behaviour(self, mocked_reindex_offer_ids, app):
        # Put 8 items in the queue, in that order: 1..8
        app.redis_client.lpush("offer_ids", *reversed(range(1, 9)))

        search.index_offers_in_queue()

        # First run pops and indexes 1, 2, 3. Second run pops and
        # indexes 4, 5, 6. And stops because there are less than
        # REDIS_OFFER_IDS_CHUNK_SIZE items left in the queue.
        # fmt: off
        assert mocked_reindex_offer_ids.mock_calls == [
            mock.call(mock.ANY, {1, 2, 3}),
            mock.call(mock.ANY, {4, 5, 6})
        ]
        # fmt: on
        assert app.redis_client.lrange("offer_ids", 0, 5) == [b"7", b"8"]

    def test_command_behaviour(self, mocked_reindex_offer_ids, app):
        # Put 8 items in the queue, in that order: 1..8
        app.redis_client.lpush("offer_ids", *reversed(range(1, 9)))

        search.index_offers_in_queue(stop_only_when_empty=True)

        # First run pops and indexes 1, 2, 3. Second run pops and
        # indexes 4, 5, 6. Third run pops 7, 8 and stops because the
        # queue is empty.
        assert mocked_reindex_offer_ids.mock_calls == [
            mock.call(mock.ANY, {1, 2, 3}),
            mock.call(mock.ANY, {4, 5, 6}),
            mock.call(mock.ANY, {7, 8}),
        ]
        assert app.redis_client.llen("offer_ids") == 0


def test_unindex_offer_ids(app):
    search_testing.search_store[1] = "dummy"
    search_testing.search_store[2] = "dummy"
    app.redis_client.hset("indexed_offers", "1", "")
    app.redis_client.hset("indexed_offers", "2", "")

    search.unindex_offer_ids([1, 2])

    assert app.redis_client.hkeys("indexed_offers") == []
    assert search_testing.search_store == {}


def test_unindex_all_offers(app):
    search_testing.search_store[1] = "dummy"
    search_testing.search_store[2] = "dummy"
    app.redis_client.hset("indexed_offers", "1", "")
    app.redis_client.hset("indexed_offers", "2", "")

    search.unindex_all_offers()

    assert app.redis_client.hkeys("indexed_offers") == []
    assert search_testing.search_store == {}
