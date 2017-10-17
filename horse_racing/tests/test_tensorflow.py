# import datetime
# import unittest
#
# import numpy as np
#
# from horse_racing.betfair_manager.query_market import find_race_to_bet
# from horse_racing.neural_networks.neural_network import query_neural_network_for_bets
# from horse_racing.utils.mongo_manager import MongoManager
#
#
# class TeensorflowTest(unittest.TestCase):
#
#     def test_tensorflow_from_na_trade(self):
#         m = MongoManager()
#         a = list(m.mongodb.tf.find({}))
#         t = a[1]['input']
#         t2 = np.array(t)
#         t2[0][0] = np.nan
#         query_neural_network_for_bets(t2.reshape(2, 2640))
