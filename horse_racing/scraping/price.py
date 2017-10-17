import datetime
import logging

import numpy as np
import pandas as pd
from tqdm import tqdm

from horse_racing.betfair_manager.bookmakers import get_race_odds
from horse_racing.betfair_manager.query_market import get_market_result
from horse_racing.utils.mongo_manager import MongoManager
from horse_racing.utils.tools import get_config

log = logging.getLogger(__name__)


def get_VWAP(volume):
    total_volume = 0
    total_price = 0
    for p in volume:
        total_volume += p.size
        total_price += p.size * p.price
    return total_price / total_volume


def collect_prices(collection_name='price_scrape', single_marketid=False):
    from horse_racing.betfair_manager.engine import Container as BFContainer
    from horse_racing.matchbook_manager.engine import Container as MBContainer

    try:
        bfm = BFContainer()
    except:
        log.error("Unable to log into betfair")

    if not single_marketid:
        try:
            mbm = MBContainer()
        except:
            log.error("Unable to log into matchbook")

    if single_marketid:
        events, markets = bfm.get_single_race(single_marketid)
    else:
        events, markets = bfm.get_all_races()

    try:
        prices = bfm.update_markets(events, markets)
    except AttributeError:
        log.info("No markets to scrape")
        return

    if not single_marketid:
        try:
            mb_prices = mbm.get_races()
        except:
            mb_prices = {}
            log.error("failed to get mb prices")
    else:
        mb_prices = {}

    event_mapping = {}
    bf_selection_name_mapping = {}
    for e, ms in markets.items():
        for m in ms:
            mb_market = None
            try:
                mb_market = mb_prices[(m[1].event.venue, m[1].market_start_time.strftime("%Y-%m-%dT%H:%M:00.000Z"))]
            except KeyError:
                log.info("Didn't find matchbook market for {}@{}".format(m[1].market_start_time,
                                                                         m[1].event.venue))
            event_mapping[m[0]] = e, m[1].market_start_time, m[1].event.country_code, mb_market
            bf_selection_name_mapping.update({r.selection_id: r.runner_name for r in m[1]['runners']})

    for p in tqdm(prices):
        # find turf bookmaker odds
        turf_odds_df = pd.DataFrame()
        race_status = {}
        for m_id, m in markets[event_mapping[p.market_id][0]]:
            if m_id != p.market_id:
                continue
            market_start_time = event_mapping[p.market_id][1]
            venue = m.event.venue.lower()
            config = get_config()
            turf_countries = config.get('Scraping', 'turf_countries').split()
            if m.event.country_code not in turf_countries:
                continue
            # TODO, check and process turf odds
            try:
                turf_odds_df, race_status = get_race_odds(venue, market_start_time, m.runners)
            except:
                pass

        mb_market = event_mapping[p.market_id][3]
        for r in p.runners:
            back_prices, back_sizes, lay_prices, lay_sizes = [-1, -1, -1], [-1, -1, -1], [-1, -1, -1], [-1, -1, -1]
            try:
                vwap = get_VWAP(r.ex.traded_volume)
            except ZeroDivisionError:
                vwap = 0.
            for i in range(3):

                try:
                    back_prices[i] = r.ex.available_to_back[i].price
                except IndexError:
                    back_prices[i] = None

                try:
                    lay_prices[i] = r.ex.available_to_lay[i].price
                except IndexError:
                    lay_prices[i] = None

                try:
                    back_sizes[i] = r.ex.available_to_back[i].size
                except IndexError:
                    back_sizes[i] = None

                try:
                    lay_sizes[i] = r.ex.available_to_lay[i].size
                except IndexError:
                    lay_sizes[i] = None

            try:
                sp_dict = {'near_price': r.sp.near_price,
                           'far_price': r.sp.far_price,
                           'actual_SP': r.sp.actual_SP,
                           'back_SP_amounts': [(a.price, a.size) for a in r.sp.back_stake_taken],
                           'lay_SP_amounts': [(a.price, a.size) for a in r.sp.back_stake_taken]}
            except:
                sp_dict = {}

            seconds_until_start = (event_mapping[p.market_id][1] - datetime.datetime.now()).total_seconds()
            event_id = event_mapping[p.market_id][0]
            d = {'marketid': p.market_id,
                 'selection_id': r.selection_id,
                 'LTP': r.last_price_traded,
                 'back_sizes0': back_sizes[0],
                 'back_prices0': back_prices[0],
                 'back_sizes1': back_sizes[1],
                 'back_prices1': back_prices[1],
                 'back_sizes2': back_sizes[2],
                 'back_prices2': back_prices[2],
                 'lay_sizes0': lay_sizes[0],
                 'lay_prices0': lay_prices[0],
                 'lay_sizes1': lay_sizes[1],
                 'lay_prices1': lay_prices[1],
                 'lay_sizes2': lay_sizes[2],
                 'lay_prices2': lay_prices[2],
                 'timestamp': datetime.datetime.now(),
                 'eventid': event_id,
                 'marketstarttime': event_mapping[p.market_id][1],
                 'countrycode': event_mapping[p.market_id][2],
                 'seconds_until_start': seconds_until_start,
                 'total_matched': r.total_matched,
                 'VWAP': vwap,
                 }
            d.update(sp_dict)
            if not turf_odds_df.empty:
                # Add the turf odds
                try:
                    bookie_prices = turf_odds_df.loc[r.selection_id].values.astype(float)
                    bookie_prices[bookie_prices == 0] = np.nan  # replace 0 with nan

                    d['bookies'] = pd.DataFrame({'name': turf_odds_df.loc[r.selection_id].index,
                                                 'price': bookie_prices}). \
                        to_dict(orient='records)')
                    d['mean_bookie_price'] = np.nanmean(bookie_prices)
                    d['median_bookie_price'] = np.nanmedian(bookie_prices)
                    d['min_bookie_price'] = np.nanmin(bookie_prices)
                    d['max_bookie_price'] = np.nanmax(bookie_prices)

                except KeyError:
                    log.info("No turf odds for selection: {}".format(r.selection_id))

            if mb_market:
                d['mb_market_id'] = mb_market['id']
                runner_name = bf_selection_name_mapping[r.selection_id]
                mb_selection_id = None
                for mr in mb_market['runners']:
                    if mr['name'].lstrip('1234567890- ') == runner_name:
                        mb_selection_id = mr['id']
                        d['mb_selection_id'] = mb_selection_id
                        d['mb_volume'] = mr['volume']
                        back_index, lay_index = 0, 0
                        for mp in mr['prices']:
                            if mp['side'] == 'back':
                                d['mb_back_prices{}'.format(back_index)] = mp['decimal-odds']
                                d['mb_back_sizes{}'.format(back_index)] = mp['available-amount']
                                back_index += 1
                            else:
                                d['mb_lay_prices{}'.format(back_index)] = mp['decimal-odds']
                                d['mb_lay_sizes{}'.format(back_index)] = mp['available-amount']
                                lay_index += 1
                if not mb_selection_id:
                    log.warning("Didn't find runner information for bf selection id {}".format(r.selection_id))

            d.update(race_status)
            log.debug(d)
            m = MongoManager()
            success = m.insert_document(collection_name, d)
            log.debug(success)


def collect_results():
    m = MongoManager()
    markets = m.mongodb_price['price_scrape'].distinct('marketid')
    all_results = m.mongodb_price['results_scrape'].distinct('marketid')
    to_get = set(markets) - set(all_results)
    log.info("To get {} results".format(len(to_get)))
    if not to_get:
        return

    results = {}

    for mk in to_get:
        results.update(get_market_result(mk))
        # time.sleep(0.2)

    log.info("Got {} results".format(len(results)))

    for k, v in results.items():
        d = {}
        winner = None
        losers = []
        for k1, v1 in v.items():
            if v1 == 'WINNER':
                winner = k1
            if v1 == 'LOSER':
                losers.append(k1)
        d.update({'marketid': k})
        d['timestamp'] = datetime.datetime.now()
        d['winner'] = winner
        d['losers'] = losers

        if winner is not None:  # filter out races that have not yet completed
            m.insert_document('results_scrape', d, database='price')
