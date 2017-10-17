import unittest

from mock import mock

import os, datetime

from horse_racing.betfair_manager.bookmakers import get_race_odds, get_odds


def turfmock(f):
    def mock_post(*args, **kwargs):
        input_file = "{}.html".format('_'.join(f.__name__.split('_')[1:]))
        with open(os.path.join(os.path.dirname(__file__),
                               'test_data',
                               'turf_data',
                               input_file), encoding='latin-1') as fn:
            raw_data = fn.read()

        class MockResponse:
            def __init__(self, *args, **kwargs):
                self.text = raw_data
                self.status_code = 200

        return MockResponse()

    def inner(*args, **kwargs):
        with mock.patch('requests.get', side_effect=mock_post):
            f(*args, **kwargs)
    return inner



class TurfScrapeTests(unittest.TestCase):

    @turfmock
    def test_oddschecker(self):
        df, race_status = get_odds("http://oddschecker/race")
        self.assertEqual(df.iloc[4,5],'12')
        self.assertEqual(df.shape, (9,28))
        self.assertEqual(race_status['Class'],'5')
        self.assertEqual(race_status['Distance'],'1m 13y')

if __name__ == '__main__':
    unittest.main()
