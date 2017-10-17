import unittest

import os
import json

from matchbook import APIClient
from mock import mock

from horse_racing.matchbook_manager.engine import Container
from matchbook.endpoints.baseendpoint import BaseEndpoint

def matchbookmock(f):
    def mock_post(*args, **kwargs):
        input_file = "{}.json".format('_'.join(f.__name__.split('_')[1:]))
        with open(os.path.join(os.path.dirname(__file__),
                               'test_data',
                               'matchbook_data',
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
        with mock.patch('matchbook.endpoints.baseendpoint.BaseEndpoint.request', side_effect=mock_post):
            f(*args, **kwargs)
    return inner

class EngineTests(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.container = Container()
        cls.container.api = APIClient('user', 'pass')
        cls.container.horse_racing = 123


    def test_sport(self):
        c = Container()

    @matchbookmock
    def test_getmarkets(self):
        pass
        # races = self.container.get_races()
        # for r in races:
        #     pass

if __name__ == '__main__':
    unittest.main()