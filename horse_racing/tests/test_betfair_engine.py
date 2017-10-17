import unittest
import os
import json
import datetime

from mock import mock

from betfair import Betfair
from betfair.constants import MarketProjection
from betfair.models import MarketFilter, TimeRange, PriceProjection
from horse_racing.betfair_manager.engine import Container, price_adjustment
from horse_racing.utils.tools import get_config


def betfairmock(f):
    def mock_post(*args, **kwargs):
        input_file = "{}.json".format('_'.join(f.__name__.split('_')[1:]))
        with open(os.path.join(os.path.dirname(__file__),
                               'test_data',
                               'betfair_data',
                               input_file), encoding='latin-1') as fn:
            json_data = json.load(fn)

        class MockResponse:
            def __init__(self, *args, **kwargs):
                self.json_data = json_data
                self.status_code = 200

            def json(self):
                return json_data

        return MockResponse()

    def inner(*args, **kwargs):
        with mock.patch('requests.Session.post', side_effect=mock_post):
            f(*args, **kwargs)
    return inner


class EngineTests(unittest.TestCase):


    @classmethod
    def setUp(cls):
        container = Container()
        cls.client = container.client
        config = get_config()
        prodkey = config.get("Betfair", "prod_app")
        certfile = config.get("Betfair", "cert_file")
        cls.client = Betfair(prodkey, certfile)
        cls.client.session_token = 'FakeSession'
        #cls.client.login(username, password)

    @betfairmock
    def test_event_types(self):
        event_types = self.client.list_event_types(
            MarketFilter(text_query='horse')
        )
        self.assertEqual(event_types[0].event_type.id,'7')

    @betfairmock
    def test_list_events(self):
        delta = datetime.timedelta(seconds=24 * 60 * 60)
        to_time = datetime.datetime.now() + delta
        events = self.client.list_events(filter=MarketFilter(event_type_ids=['7'],
                                                             market_countries=['GB', 'IRL'],
                                                             market_start_time=TimeRange(to=to_time)))
        self.assertEqual(len(events), 6)
        self.assertEqual(events[2].event.id, '3453086')
        self.assertEqual(events[3].event.open_date,datetime.datetime(2017, 10, 25, 15, 30))

    @betfairmock
    def test_list_markets(self):
        markets = self.client.list_market_catalogue(MarketFilter(event_ids=[123, 456, 789],
                                                                 market_type_codes=['WIN']),
                                                    market_projection=[MarketProjection['RUNNER_DESCRIPTION'],
                                                                       MarketProjection['EVENT'],
                                                                       MarketProjection['MARKET_DESCRIPTION'],
                                                                       MarketProjection['MARKET_START_TIME']
                                                                       ])
        self.assertEqual(len(markets),27)
        self.assertEqual(len(markets[13].runners),9)
        self.assertEqual(markets[26].runners[1].selection_id, 13161326)

    @betfairmock
    def test_update_prices(self):
        pp = PriceProjection(price_data=['EX_BEST_OFFERS', 'EX_TRADED'])
        markets = self.client.list_market_book(market_ids=[123.456], price_projection=pp)
        self.assertEqual(len(markets),4)
        self.assertEqual(markets[0].runners[0].ex.traded_volume[7].size, 130.28)
        self.assertEqual(markets[2].runners[2].last_price_traded, 6.2)
        self.assertEqual(markets[3].runners[5].ex.available_to_back[1].values(), [16.5,2.6])

    def test_price_adjustment(self):
        self.assertEqual(130, price_adjustment(123.2))
        self.assertEqual(34, price_adjustment(33.3333))

if __name__ == '__main__':
    unittest.main()