# get list of past races

# evaluation predictions

# assess profit

# statistical analysis
from horse_racing.backtesting.betf_race import BetFairRace
from horse_racing.utils.mongo_manager import MongoManager
import pandas as pd
import datetime as dt
import time
import json

nanos_to_days = (60. * 60 * 24 * 100000000)

def get_races(collection):
    for r in collection.find( projection= {'_id': False}):
        yield r['eventId'], BetFairRace.from_json(json.dumps(r))

def get_race_data(race, race_df):
    """
    Try and find the race Id
    :param race: 
    :param race_df: 
    :return: 
    """
    race_time = dt.datetime.strptime(race.marketTime,"%Y-%m-%dT%H:%M:%S.000Z")
    #race_date = time.mktime(race_time.date())
    races = race_df[(race_df['RACEDATE']==race_time.date()) & (race_df['RACETIME']==race_time.strftime("%H:%M"))
                                                               & (race_df['NUMBEROFRUNNERS'] == len(race.runners))]
    if races.empty:
        race.race_number = None
        return race
    else:
        if len(races.index)> 1:
            print(races)
            race.race_number = None
            return race
        #return 1
        race.race_number = races.iloc[0]['RACENUMBER']
    return race


def race_dataframes(max_runners, slice_hours):

    m = MongoManager()
    collection = m.mongodb_price.get_collection("Backtesting")
    m.mongodb_price.drop_collection("OddsTS2017")
    odds_collection = m.mongodb_price.get_collection("OddsTS2017")
    winner_sps = []
    for k,r in get_races(collection):
        try:
            if len(r.runners) > max_runners:
                # Too many runners in this race
                continue
            if dt.datetime.strptime(r.marketTime, "%Y-%m-%dT%H:%M:%S.%fZ") < dt.datetime(2017,1,1):
                continue
            #winner_sps.append((r.marketId, r.get_starting_prices()[r.get_winner()]))
            race_odds_df = r.get_hours_before(hours=slice_hours)
            race_odds_df.index = race_odds_df.index.map(lambda x: x.to_datetime().strftime("%H:%M"))
            #winner_index = list(r.get_odds_dataframe().columns).index(r.get_winner())
            odds_collection.insert_one({'ts': race_odds_df.to_dict(), 'winner' : r.get_winner()})
        except:
            continue
    pd.DataFrame.from_records(winner_sps)

if __name__ == '__main__':
    race_dataframes(max_runners=50,slice_hours=1)
