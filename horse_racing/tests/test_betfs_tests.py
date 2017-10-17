# todo: make this test pass (bfextract.json is missing)
# import unittest
#
# from horse_racing.legacy.backtesting.betf_race import BetFairRace
#
# class BetfsTests(unittest.TestCase):
#
#     @classmethod
#     def setUp(cls):
#         with open('./test_data/bfextract.json') as f:
#             cls.json_string = f.read()
#
#     def testLoadJson(self):
#         bf_race = BetFairRace.create_from_json(self.json_string)
#         t_df = bf_race.get_odds_dataframe()
#         self.assertEqual(t_df.shape, (441, 14))
#         self.assertEqual(bf_race.get_starting_prices(name=False)[8783853], 13.5)
#         self.assertEqual(bf_race.get_winner(name=True), 'Stun Gun')
#
#     def testSerialize(self):
#         bf_race = BetFairRace.create_from_json(self.json_string)
#         bf_race2 = BetFairRace.from_json(bf_race.to_json())
#         t_df = bf_race2.get_odds_dataframe()
#         self.assertEqual(t_df.shape, (441, 14))
#         self.assertEqual(bf_race2.get_starting_prices(name=False)[8783853], 13.5)
#         self.assertEqual(bf_race2.get_winner(name=True), 'Stun Gun')