import datetime
import os
import unittest

import numpy as np
import pandas as pd
from mock import MagicMock, patch
import pickle
import json

from horse_racing.betfair_manager.bet_logic import BetLogic
from horse_racing.betfair_manager.engine import place_bets
from horse_racing.betfair_manager.query_market import find_race_to_bet
from horse_racing.neural_networks.neural_network_launcher import query_neural_network_for_bets
from horse_racing.utils.mongo_manager import MongoManager


class PlaceBets(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.mongodb = MongoManager(use_archive=True)

    def test_mongo_get_bets1(self):
        m = MongoManager(use_archive=False)
        m.reconnect(use_archive=False)
        data = self.mongodb.get_ts_for_races_about_to_start(now=datetime.datetime.strptime(
            '2018-02-28 16:54:15',
            "%Y-%m-%d %H:%M:%S"))
        self.assertEqual(1, len(data))

    def test_mongo_get_bets0(self):
        m=MongoManager(use_archive=False)
        m.reconnect(use_archive=False)
        data = self.mongodb.get_ts_for_races_about_to_start(now=datetime.datetime.strptime(
            '2014-02-28 16:54:15',
            "%Y-%m-%d %H:%M:%S"))
        self.assertEqual(0, len(data))

    def _place_bet(self, date):
        """race available to bet, return bet instructions"""
        races_arr, selection_ids, market_ids, event_ids, race_start_times = \
            find_race_to_bet(now=datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S"))

        self.assertEqual(1, len(races_arr))
        self.assertFalse(np.isnan(np.sum(races_arr)))  # array doesn't return nan
        self.assertLessEqual(len(races_arr[0]), 540)  # max 9x60 entries
        self.assertGreaterEqual(len(selection_ids[0]), 1)  # some horses
        self.assertGreaterEqual(len(event_ids[0]), 1)  # some event ids
        self.assertGreaterEqual(len(race_start_times), 1)  # some race start times
        ltps = np.array([[22, 2, 4, 5, 67, 0, 1, 1, 1, 1.5], [45, 2, 1, 1, 1, 1, 1, 1, 1, 1.5]]).reshape(2,10)
        races_arr = ltps
        bets = query_neural_network_for_bets(races_arr)[0]  # model name now returned as 1st argument

        self.assertEqual(len(bets), 2)
        self.assertTrue(True in bets)
        self.assertTrue(False in bets)
        self.assertTrue(market_ids is not None)

        # neutralize writing to db through MagicMock
        with patch('horse_racing.betfair_manager.engine.MongoManager'):
            prices = (races_arr, races_arr, races_arr, races_arr, races_arr, races_arr, races_arr)
            place_bets(bets, np.array(selection_ids),
                       prices,
                       market_ids[0], event_ids[0], race_start_times[0],
                       None)

    def test_place_bet1(self):
        m = MongoManager(use_archive=False)
        m.reconnect(use_archive=False)
        self._place_bet('2018-02-28 16:54:15')

    def test_place_bet2(self):
        m = MongoManager(use_archive=False)
        m.reconnect(use_archive=False)
        self._place_bet('2018-02-28 16:54:15')

    def test_no_races_to_bet(self):
        """ no race to bet"""
        races_arr, selection_ids, market_ids, event_ids, race_start_times = find_race_to_bet(
            now=datetime.datetime.strptime("2017-02-28 10:59:00", "%Y-%m-%d %H:%M:%S"))

        self.assertEqual(None, races_arr)

    def test_bet_logic(self):
        # mock place_bers with mock
        with patch('horse_racing.betfair_manager.bet_logic.place_bets') as mock_p, \
                patch('horse_racing.betfair_manager.bet_logic.Container') as mock_Container:
            # each Container function  can to be a MagicMock object with assigned return value,
            m = MagicMock()
            m.get_race_status.return_value = pd.read_json(os.path.join(os.path.dirname(__file__),
                                                                       'test_data',
                                                                       'race_status.json'))
            with open(os.path.join(os.path.dirname(__file__), 'test_data', 'single_market.pickle'), 'rb') as f:
                resp = pickle.load(f)
            m.get_single_market.return_value = resp
            mock_Container.return_value = m
            b = BetLogic()
            b.update_prices_and_place_bet(MagicMock(),
                                          np.arange(60 * 12).reshape(1, -1),
                                          [[r.selection_id for r in resp[0].runners]],
                                          ['1.138963969'],
                                          ['28548440'],
                                          race_start_times=[datetime.time(18, 10)])

            mock_p.assert_called_once()

    def test_get_last_LTPs(self):
        m = MongoManager(use_archive=True)
        m.reconnect(use_archive=False)
        now = datetime.datetime.strptime('2018-02-28 16:54:15', "%Y-%m-%d %H:%M:%S")
        LTPs = m.get_last_LTPs(selection_id=16377754,
                               amount_of_prices=3,
                               now=now)
        self.assertEqual(len(LTPs), 3)


# class UpdateBets(unittest.TestCase):
#
#     @classmethod
#     def setUp(cls):
#         cls.mongodb = MongoManager(use_archive=True)
#
#     def test_update_placed_orders(self):
#         b = BetLogic()
#         b.update_placed_orders()
