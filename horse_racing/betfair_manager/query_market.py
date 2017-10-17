import datetime as dt
import json
import logging

import numpy as np
import pandas as pd
import requests

from horse_racing.utils.mongo_manager import MongoManager

log = logging.getLogger(__name__)


def reformat_to_array(races, features_per_horse=60):
    # todo: this is not needed anymore unless we use historical data for tensorflow
    """ Reformat pre-betting data for races starting within 1 minutes according to the training dataset """

    selection_ids = []
    market_ids = []
    event_ids = []
    race_start_times = []
    max_no_horses = max([len([y for y in races[x].keys() if type(y) == int]) for x in races])
    array = np.zeros(shape=(len(races), features_per_horse * max_no_horses))
    row = -1

    for race in races:
        market_ids.append(race)
        event_ids.append(races[race]['EventID'])
        race_start_times.append(races[race]['RaceStartTime'])

        row += 1
        horses = [x for x in races[race] if type(x) == int]
        ts = np.empty(0)

        for i in range(len(horses)):
            current_horse_ts = races[race][horses[i]][::-1].values
            missing_quotes = features_per_horse - len(current_horse_ts)
            if missing_quotes < 0:
                log.error("Potential duplicate last-hour-quotes identified for race %s - horse %s!" %
                          (race, horses[i]))
                break
            current_horse_ts = np.append(current_horse_ts, np.array([np.nan] * missing_quotes))
            ts = np.concatenate((ts, current_horse_ts))
        array[row, :len(ts)] = ts
        selection_ids.append(horses)
    array[np.isnan(array)] = 0
    return array, selection_ids, market_ids, event_ids, race_start_times


def find_race_to_bet(now=None, min_before_start=0, countrycodes=['GB','IE']):
    """ Returns races that will start within the next minute as numpy array to be passed into make_bet_recommendation"""

    log.debug("Start downloading races to bet")
    now = dt.datetime.now() if not now else now
    m = MongoManager()
    data = m.get_ts_for_races_about_to_start(now, countrycodes, min_before_start)

    # Group quotes by race ($marketid) and horse ($selection_id)
    # Fallback to back_prices0 if LTP = None (no traded price)
    races = {}

    for race in data:
        race_dict = {}
        horses = sorted(list(set([x['Horse'] for x in race['TS']])))
        race_start_time = sorted(list(set([x['RaceStartTime'] for x in race['TS']])))
        race_event_id = sorted(list(set([x['EventID'] for x in race['TS']])))

        if len(race_start_time) != 1:
            log.warning("Inconsistent start time for race %s! Double check its quotes!" % race['_id'])

        race_dict['RaceStartTime'] = race_start_time[0]
        race_dict['EventID'] = race_event_id[0]
        race_dict['SelectionIds'] = horses

        for horse in horses:  # todo: this is inconsistent with training
            ts = pd.Series(
                {x['Time']: x['LTP'] if x['LTP'] else x['BestBack'] for x in race['TS'] if x['Horse'] == horse})

            # Check/log NaNs ratio if significant
            try:
                if float(np.count_nonzero(np.isnan(ts)) / len(ts)) >= 0.25:
                    log.warning("NaNs ratio >= 25%% found for TS for MarketID: %s - EventID: %s - SelectionID: %s!" % \
                                (race['_id'], race_dict['EventID'], horse))
            except:
                log.warning("All entries None in  TS for MarketID: %s - EventID: %s - SelectionID: %s!" % \
                            (race['_id'], race_dict['EventID'], horse))

            race_dict[horse] = ts

        races[race['_id']] = race_dict

    if not races:
        log.debug("No races available for betting!")
        return None, None, None, None, None

    races_arr, selection_ids, market_ids, event_ids, race_start_times = reformat_to_array(races)

    return races_arr, selection_ids, market_ids, event_ids, race_start_times


def get_market_result(market_id):
    url = "https://www.betfair.com/www/sports/exchange/readonly/v1/bymarket"
    if isinstance(market_id, (tuple, list)):
        marketIds = ",".join(map(str, market_id))
    else:
        marketIds = market_id
    args = {'_ak': 'nzIFcwyWhrlwYMrh',
            'currencyCode': 'GBP',
            'locale': 'en_GB',
            'marketIds': marketIds,
            'rollupLimit': 2,
            'rollupModel': 'STAKE',
            'types': 'MARKET_STATE, RUNNER_STATE'}
    r = requests.get(url, args)  # headers={'accept':'application/xml'})
    data = json.loads(r.text)
    results_dict = {}
    for et in data['eventTypes']:
        for e in et['eventNodes']:
            for m in e['marketNodes']:
                if m['state']['status'] == 'OPEN':
                    continue
                results_dict[m['marketId']] = {}
                for rn in m['runners']:
                    results_dict[m['marketId']][rn['selectionId']] = rn['state']['status']
    return results_dict


if __name__ == '__main__':
    # races = find_race_to_bet()
    # bets = make_bet_recommendation(races[0])
    rd = get_market_result(1.138299759)
    print(rd['1.138130951'][7157214])
    rd2 = get_market_result([1.138130966, 1.138130971])
    print(rd2['1.138130966'][15663402])
