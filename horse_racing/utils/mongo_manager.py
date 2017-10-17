'''
Functions that are used to log and analyse present and past bets
'''

import logging
import socket
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm

from horse_racing.utils.tools import get_config

hostname = socket.gethostname()

log = logging.getLogger(__name__)


class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


class MongoManager(object, metaclass=Singleton):
    def __init__(self, use_remote=True, use_archive=False):

        # to create a local copy, run mongod locally with shell and copy over the remote with this command in mongodb
        # db.copyDatabase("horse_racing","horse_racing","dickreuter.com","rj","rj","SCRAM-SHA-1" )
        # to run it automatically as service in windows, do this with admin rights: mongod --install

        config = get_config()
        prod = config.get("Servers", "prod")
        remote_server = config.get("MongoDB", "remote_server")

        # use localhost when program runs on prod:
        localhost = config.get("MongoDB", "localhost")

        # database for price operations
        price_db = config.get("MongoDB", "price_db")
        price_login = config.get("MongoDB", "price_login")
        price_pass = config.get("MongoDB", "price_pass")
        price_login_write = config.get("MongoDB", "price_login_write")
        price_pass_write = config.get("MongoDB", "price_pass_write")

        # database for pnl operations
        pnl_db = config.get("MongoDB", "pnl_db")
        pnl_login = config.get("MongoDB", "pnl_login")
        pnl_pass = config.get("MongoDB", "pnl_pass")
        pnl_login_write = config.get("MongoDB", "pnl_login_write")
        pnl_pass_write = config.get("MongoDB", "pnl_pass_write")

        # database for archive
        archive_db = config.get("MongoDB", "archive_db")
        archive_login_write = config.get("MongoDB", "archive_login_write")
        archive_pass_write = config.get("MongoDB", "archive_pass_write")

        if use_archive:  # use archive for everything
            # database for price operations
            price_db = archive_db
            price_login = archive_login_write
            price_pass = archive_pass_write
            price_login_write = archive_login_write
            price_pass_write = archive_pass_write

            # database for pnl operations
            pnl_db = archive_db
            pnl_login = archive_login_write
            pnl_pass = archive_pass_write
            pnl_login_write = archive_login_write
            pnl_pass_write = archive_pass_write

        if use_remote:
            if hostname == prod:
                self.mongoclient_price = MongoClient(
                    'mongodb://{}:{}@{}/{}'.format(price_login_write,
                                                   price_pass_write,
                                                   localhost,
                                                   price_db))
                self.mongoclient_pnl = MongoClient(
                    'mongodb://{}:{}@{}/{}'.format(pnl_login_write,
                                                   pnl_pass_write,
                                                   localhost,
                                                   pnl_db))

                self.mongoclient_archive = MongoClient(
                    'mongodb://{}:{}@{}/{}'.format(archive_login_write,
                                                   archive_pass_write,
                                                   localhost,
                                                   archive_db))

            else:
                self.mongoclient_price = MongoClient('mongodb://{}:{}@{}/{}'.format(price_login,
                                                                                    price_pass,
                                                                                    remote_server,
                                                                                    price_db))
                self.mongoclient_pnl = MongoClient('mongodb://{}:{}@{}/{}'.format(pnl_login,
                                                                                  pnl_pass,
                                                                                  remote_server,
                                                                                  pnl_db))
                self.mongoclient_archive = MongoClient('mongodb://{}:{}@{}/{}'.format(archive_login_write,
                                                                                      archive_pass_write,
                                                                                      remote_server,
                                                                                      archive_db))
        else:
            self.mongoclient_price = MongoClient('mongodb://localhost/horse_racing')
            self.mongoclient_pnl = MongoClient('mongodb://localhost/horse_racing')
            self.mongoclient_archive = MongoClient('mongodb://localhost/archive')

        self.mongodb_price = self.mongoclient_price[price_db]
        self.mongodb_pnl = self.mongoclient_pnl[pnl_db]
        self.mongodb_archive = self.mongoclient_archive[archive_db]

    def reconnect(self, use_remote=True, use_archive=False):
        self.__init__(use_remote, use_archive)

    def upload_dataframe(self, df, collection_name, database='archive'):
        if database == 'price':
            db = self.mongodb_price
        if database == 'pnl':
            db = self.mongodb_pnl
        if database == 'archive':
            db = self.mongodb_archive
        db[collection_name].insert_many(df.to_dict('records'))

    def get_dataframe(self, collection_name, max_rows=0, use_price_db=False):
        db = self.mongodb_price if use_price_db == True else self.mongodb_archive
        input_data = db[collection_name]
        data = pd.DataFrame(list(input_data.find().limit(max_rows)))
        return data

    def download_enriched_TS(self, from_year, to_year, countrycode, max_rows=999999999, col='price_scrape_enriched'):
        query = self.mongodb_price[col].aggregate(
            [{'$match': {'$and': [{"marketstarttime": {"$gte": from_year}},
                                  {"marketstarttime": {"$lte": to_year}},
                                  {'countrycode': {"$in": countrycode}}
                                  ]
                         }
              },
             {'$limit': max_rows}])

        return pd.DataFrame(list(query))

    def download_full_TS(self, from_year, to_year, countrycode, max_rows=999999999):
        query = self.mongodb_price.OddsTS.aggregate(
            [{'$match': {'$and': [{"marketstarttime": {"$gte": from_year}},
                                  {"marketstarttime": {"$lte": to_year}},
                                  {'countrycode': {"$in": countrycode}}
                                  ]
                         }
              },
             {'$limit': max_rows}])

        return list(query)

    def download_raw_prices(self, from_dt, marketids, collection='price_scrape', max_rows=9999999,
                            has_bookie=[True, False]):

        query = self.mongodb_price[collection].aggregate(
            [{'$match': {"marketid": {"$in": marketids},
                         "timestamp": {"$gte": from_dt},
                         "winner": {"$exists": True},
                         "mean_bookie_price": {"$exists": {"$in": has_bookie}}}},
             {"$project": {"_id": 0}},
             {'$limit': max_rows}])

        return list(query)

    def insert_document(self, collection_name, entry, database='price'):
        if database == 'price':
            success = self.mongodb_price[collection_name].insert_one(entry)
        elif database == 'pnl':
            success = self.mongodb_pnl[collection_name].insert_one(entry)
        return success

    def insert_list_of_documents(self, collection_name, entries, database='price'):
        if database == 'price':
            self.mongodb_price[collection_name].insert_many(entries)
        elif database == 'pnl':
            self.mongodb_pnl[collection_name].insert_many(entries)

    def get_ts_group_by_races(self):
        data = self.mongodb_price.OddsTS_flat.aggregate(
            [{"$group": {"_id": "$race_number", "odds": {"$push": "$$ROOT"}}},
             {"$project": {"_id": 0}}
             ],
            allowDiskUse=True)

    def get_all_races_ts(self):
        """ Show all races we collected the ts elements for 60min before start
        useful for backtesting """
        query = self.mongodb_price.price_scrape.aggregate([{'$match': {'seconds_until_start': {'$lt': 3600}}},
                                                           {'$group': {'_id': '$marketid',
                                                                       'TS': {'$push': {'LTP': '$LTP',
                                                                                        'BestBack': '$back_prices0',
                                                                                        'Horse': '$selection_id',
                                                                                        'Time': '$timestamp',
                                                                                        'SecondsToStart': '$seconds_until_start',
                                                                                        'RaceStartTime': '$marketstarttime'}}
                                                                       }
                                                            }
                                                           ]
                                                          )
        return list(query)

    def get_secs_to_start(self, market_id):
        data = self.mongodb_price.price_scrape.find({'marketid': market_id})
        data = list(data)[0]
        start = data['marketstarttime']
        now = datetime.now()
        return (start - now).total_seconds()

    def get_ts_for_races_about_to_start(self, now=None, countrycodes=['GB', 'IE'], min_before_start=0):
        """ show 60min ts for races that start within 1 min from now and in the future """
        now = datetime.now() if not now else now
        offset = timedelta(minutes=min_before_start)

        data = self.mongodb_price.price_scrape.aggregate(
            [{'$match': {'marketstarttime': {'$lte': now + offset + timedelta(minutes=1),
                                             '$gt': now + offset},
                         'timestamp': {'$gt': now - timedelta(minutes=60),
                                       '$lte': now},
                         'countrycode': {'$in': countrycodes}

                         }
              },
             {'$group': {'_id': '$marketid',
                         'TS': {'$push': {'LTP': '$LTP',
                                          'BestBack': '$back_prices0',
                                          'Horse': '$selection_id',
                                          'Time': '$timestamp',
                                          'SecondsToStart': '$seconds_until_start',
                                          'RaceStartTime': '$marketstarttime',
                                          'MarketID': '$marketid ',
                                          'EventID': '$eventid'}}
                         }
              }
             ], allowDiskUse=True
        )

        return list(data)

    def get_ts_grouped_by_race_and_horse(self):
        """ full mongodb solution to group races and then horses and then ts for all races last 60min"""
        data = self.mongodb_price.price_scrape.aggregate([{
            '$match': {
                'seconds_until_start': {
                    '$lt': 3600
                }
            }
        },
            {
                '$group': {
                    '_id': {
                        'race': '$marketid',
                        'horse': '$selection_id',
                        'hour': {
                            '$hour': '$timestamp'
                        },
                        'minutes': {
                            '$minute': '$timestamp'
                        },

                    },
                    'TS': {
                        '$first': '$$ROOT'
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'race': '$_id.race',
                        'horse': '$_id.horse'
                    },
                    'hoses_races': {
                        '$push': '$$ROOT'
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'race': '$_id.race'
                    },
                    'Horses': {
                        '$push': '$$ROOT'
                    }
                }
            }])

        return list(data)

    def update_document(self, collection_name, id_name, id_value, field_name, field_value, as_array=False, multi=False):
        operator = '$push' if as_array else '$set'
        self.mongodb_pnl[collection_name].update(
            {id_name: id_value},
            {operator:
                 {field_name: field_value}
             }, multi=multi
        )

    def update_document2(self, collection_name, id_name, id_value, id_name2, id_value2, field_name, field_value,
                         as_array=False, multi=False):
        """ update document maching two identifiers """
        operator = '$push' if as_array else '$set'
        self.mongodb_pnl[collection_name].update(
            {'$and': [{id_name: id_value},
                      {id_name2: id_value2}]},
            {operator:
                 {field_name: field_value}
             }
            , multi=multi
        )

    def update_orders(self, event_id, selection_id, market_id, status, price_matched, price_requested, size_settled,
                      profit):
        self.mongodb_pnl['orders'].update(
            {'$and': [
                {'event_id': event_id},
                {'selection': selection_id},
                {'market_id': market_id}]},

            {'$set': {
                'bf_result': status,
                'bf_price_matched': price_matched,
                'bf_price_requested': price_requested,
                'bf_size_settled': size_settled,
                'bf_profit': profit
            },
            }

        )

    def update_order_price(self, market_id, selection_id, bet_id, min_to_start, new_price):
        self.mongodb_pnl['orders'].update(
            {'$and': [
                {'selection': selection_id},
                {'market_id': market_id},
                {'betid': bet_id}]},

            {
                '$set': {
                    'updated': True,
                    'price': new_price},

                '$push': {
                    'updated_prices': new_price,
                    'min_to_start': min_to_start,
                },
            }
        )

        self.mongodb_pnl['place_bets'].update(
            {
                'market_id': market_id
            },
            {
                '$set': {
                    'updated': True,
                    'last_updated_min_before_start': min_to_start},

                '$push': {
                    'updated_prices': new_price,
                    'updated_min_to_start': min_to_start,
                    'updated_selection_ids': selection_id}
            }
        )

    def get_races_without_results(self):
        query = self.mongodb_pnl.place_bets.aggregate(
            [{'$match': {'winner': {'$exists': False}}

              },
             {"$project": {"market_id": 1}}

             ]
        )
        return list(query)

    def get_price_scrape_without_results(self, from_date, col='price_scrape'):
        query = self.mongodb_price[col].aggregate(
            [{"$match": {'timestamp': {'$gte': from_date}}},
             {"$group": {
                 "_id": "$marketid",
                 "winner": {"$push": "$winner"}}},
             {"$match": {"winner": {"$size": 0}}},
             {"$project": {"_id": 1}}
             ], allowDiskUse=True
        )
        return [d['_id'] for d in query]

    def load_race_results(self, market_ids):
        query = self.mongodb_price.results_scrape.find({'marketid': {"$in": market_ids}})
        return list(query)

    def update_placed_bet_with_result(self, market_id, winner_id, loser_ids):
        self.mongodb_pnl.place_bets.update(
            {"market_id": market_id},
            {"$set":
                 {'winner': winner_id,
                  'losers': loser_ids}
             }
        )

    def update_price_scrape_with_result(self, col, market_id, winner_id, loser_ids):
        self.mongodb_price[col].update(
            {"marketid": market_id,
             "selection_id": winner_id
             },
            {"$set":
                 {'winner': True,
                  'loser': False}
             },
            multi=True
        )

        self.mongodb_price[col].update(
            {"marketid": market_id,
             "selection_id": {"$in": loser_ids}
             },
            {"$set":
                 {'winner': False,
                  'loser': True}
             },
            multi=True
        )

    def recently_placed_bets(self, market_id):
        """ Retrieve last placed bets """
        query = self.mongodb_pnl.place_bets.find({'market_id': market_id})
        return list(query)[0]

    def placed_bets(self, start=datetime.now() - timedelta(hours=24), end=datetime.now()):
        query = self.mongodb_pnl.place_bets.aggregate(
            [{'$match': {'$and': [{'timestamp': {'$gt': start}},
                                  {'timestamp': {'$lte': end}}
                                  ]
                         }
              }
             ]
        )
        return list(query)

    def update_placed_bet_with_pnl(self, market_id, pnl_back, pnl_lay):
        self.mongodb_pnl.place_bets.update(
            {"market_id": market_id},
            {"$set":
                 {'pnl_back': pnl_back,
                  'pnl_lay': pnl_lay,
                  'pnl_total': pnl_back + pnl_lay}
             }
        )

    def get_bets_to_calculate_pnl(self, overwrite_calculated_pnls=False):
        """ Retrieve all bets requiring pnl calculation, having a winner but no pnl_total"""
        query = self.mongodb_pnl.place_bets.aggregate(
            [{'$match': {'$and': [{'pnl_total': {'$exists': overwrite_calculated_pnls}},
                                  {'winner': {'$exists': True}},
                                  ]
                         }
              }
             ]
        )
        return list(query)

    def get_unfilled_orders(self, start=None, end=None):
        start = datetime.now() - timedelta(hours=24) if not start else start
        end = datetime.now() if not end else end

        query = self.mongodb_pnl.orders.aggregate(
            [{'$match': {'$and': [{'timestamp': {'$gt': start}},
                                  {'timestamp': {'$lte': end}},
                                  {'bf_result': {'$exists': False}}
                                  ]
                         }
              },
             ]
        )
        return list(query)

    def get_all_orders(self, start=None, end=None):
        start = datetime.now() - timedelta(hours=24) if not start else start
        end = datetime.now() if not end else end
        query = self.mongodb_pnl.orders.aggregate(
            [{'$match': {'$and': [{'timestamp': {'$gt': start}},
                                  {'timestamp': {'$lte': end}},
                                  ]
                         }
              },
             ]
        )

        return list(query)

    def get_total_pnl(self, start=None, end=None):
        """ Retrieve total pnl according to provided temporal limits """
        start = datetime.now() - timedelta(hours=24) if not start else start
        end = datetime.now() if not end else end

        query = self.mongodb_pnl.place_bets.aggregate(
            [{'$match': {'$and': [{'timestamp': {'$gt': start}},
                                  {'timestamp': {'$lte': end}}
                                  ]
                         }
              },
             {"$group": {"_id": "null",
                         "sum_total": {"$sum": "$pnl_total"},
                         "sum_back": {"$sum": "$pnl_back"},
                         "sum_lay": {"$sum": "$pnl_lay"},
                         "bf_profit": {"$sum": "$bf_profit"},
                         }
              }
             ]
        )

        return list(query)[0]

    def get_pnl_per_race_from_orders(self, start=None, end=None):
        """ group orders into races and get total pnl """
        start = datetime.now() - timedelta(hours=24) if not start else start
        end = datetime.now() if not end else end

        query = self.mongodb_pnl.orders.aggregate(
            [{'$match': {'$and': [{'timestamp': {'$gt': start}},
                                  {'timestamp': {'$lte': end}}
                                  ]
                         }
              },

             {"$group": {"_id": "$market_id",
                         "bf_profit": {"$sum": "$bf_profit"}
                         }
              }
             ]
        )

        return list(query)

    def get_all_pnl(self, start=None, end=None):
        start = datetime.now() - timedelta(hours=24) if not start else start
        end = datetime.now() if not end else end
        """ Retrieve pnl for all the recorded bets """

        query = self.mongodb_pnl.place_bets.aggregate(
            [{'$match': {'$and': [{'timestamp': {'$gt': start}},
                                  {'timestamp': {'$lte': end}}
                                  ]
                         }
              },
             {"$project": {"_id": 0,
                           "sum_total": "$pnl_total",
                           "sum_back": "$pnl_back",
                           "sum_lay": "$pnl_lay",
                           "bf_profit": "$bf_profit"}}
             ]
        )

        return list(query)

    def get_last_LTPs(self, selection_id, amount_of_prices, now=None):
        now = datetime.now() if not now else now
        """ Get the last 3 LTPs for a horse """

        query = self.mongodb_price.price_scrape.aggregate(
            [{'$match': {'$and': [{'selection_id': selection_id},
                                  {'timestamp': {'$lte': now}}
                                  ]
                         }
              },
             {'$limit': amount_of_prices},
             {"$group": {
                 "_id": None,
                 "LTPs": {"$push": "$LTP"}
             }}
             ])

        return list(query)[0]['LTPs']

    def upcoming_races(self, start_from=None):
        start_from = datetime.now() if not start_from else start_from
        """ show upcoming races """

        query = self.mongodb_price.price_scrape.aggregate(
            [{'$match': {'marketstarttime': {'$gte': start_from}}},
             {"$group": {
                 "_id": "$marketstarttime",
                 "Number of prices": {"$sum": 1},
                 "Countrycode": {"$first": "$countrycode"}
             }},
             {'$sort': {'_id': 1}},
             {'$project': {"Start": "$_id",
                           "Number of prices": 1,
                           "Countrycode": 1,
                           "_id": 0}}

             ])

        return list(query)

    def retrieve_bookie_prices(self):
        query = self.mongodb_price.price_scrape.aggregate(
            [

                {"$match": {"bookies": {"$exists": "true"}}
                 },
                {"$unwind": "$bookies"
                 },
                {"$match": {"bookies.name": "Sky Bet"}
                 },
                {"$project": {"bookies_value": "$bookies.price", "LTP": 1, "back_prices0": 1, "lay_prices0": 1,
                              "median_bookie_price": 1, "mean_bookie_price": 1
                              }},

            ]
        )
        return list(query)

    def get_betfair_matchbook_1min_before_start(self):
        query = self.mongodb_price.price_scrape.aggregate([
            {
                "$match": {"bookies": {"$exists": "true"},
                           "seconds_until_start": {"$lt": 60}}
            },

            {"$unwind": "$bookies"
             },
            {"$project": {"bookies_value": "$bookies.price", "bookies_name": "$bookies.name",
                          "LTP": 1, "back_prices0": 1, "lay_prices0": 1, "median_bookie_price": 1,
                          "seconds_until_start": 1,
                          "mean_bookie_price": 1, "diff": {"$subtract": ["$lay_prices0", "$bookies.price"]}}
             },

            {"$match": {"diff": {"$lt": 0},
                        "bookies_name": "Matchbook"}
             },

        ])
        return list(query)

    def get_latest_date_in_enriched_prices(self, collection):
        query = self.mongodb_price[collection].aggregate([
            {"$sort": {"marketstartdate": -1}},
            {"$limit": 1}
        ])

        return list(query)[0]

    def get_distinct(self, field, col, from_date, must_have_bookie):
        if must_have_bookie:
            query = self.mongodb_price[col].distinct(field,
                                                     {"timestamp": {"$gt": from_date},
                                                      "mean_bookie_price": {"$exists": True}}
                                                     )
        else:
            query = self.mongodb_price[col].distinct(field,
                                                     {"timestamp": {"$gt": from_date}}
                                                     )
        return set(query)

    def get_avg_ltp_by_time_to_start_bucketed(self, field, metric, boundaries, from_date, to_date, countrycode,
                                              col='price_scrape'):
        query = self.mongodb_price[col].aggregate([

            {
                "$match": {"winner": True,
                           "timestamp": {"$gt": from_date, "$lt": to_date},
                           "LTP": {"$ne": np.nan},
                           "countrycode": {"$in": countrycode}}
            },

            {
                "$bucket": {
                    "groupBy": "$seconds_until_start",
                    "boundaries": boundaries,
                    "default": "other",
                    "output": {
                        "avg_ltp": {"$" + metric: "$" + field}
                    }
                }
            }

        ],
            allowDiskUse=True)
        return list(query)

    def correct_seconds_until_start(self, col):
        """ this function is no longer needed as both price_scrape and price_scrape_tickdata have been corrected"""
        documents = self.mongodb_price[col].aggregate([
            {"$project": {
                "secs": {"$divide": [{"$subtract": ["$marketstarttime", "$timestamp"]}, 1000]}}}

        ])

        for d in tqdm(documents, total=4300000):
            self.mongodb_price[col].update(
                {"_id": d['_id']},
                {"$set":
                     {"seconds_until_start": d['secs']}
                 }
            )
