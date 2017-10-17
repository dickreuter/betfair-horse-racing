import unittest
from datetime import datetime

from horse_racing.utils.mongo_manager import MongoManager


class EvaluateBets(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.mongodb = MongoManager(use_archive=True)

    def test_get_result_eval1(self):
        data = self.mongodb.get_bets_to_calculate_pnl(True)
        self.assertGreater(len(data), 1)

    def test_get_result_eval3(self):
        data = self.mongodb.get_all_pnl(datetime.strptime('2018-01-13 11:59:30', "%Y-%m-%d %H:%M:%S"),
                                        datetime.strptime('2100-01-21 18:59:30', "%Y-%m-%d %H:%M:%S"))
        self.assertGreater(len(data), 1)

# not working from server
# class BetfairSettlements(unittest.TestCase):
#
#     @classmethod
#     def setUp(cls):
#         cls.mongodb = MongoManager()
#
#     def test_dowwnload_settlements(self):
#         c = Container()
#         df, commission = c.get_cleared_orders()
#         self.assertGreater(len(df),0)
#         print(df)
