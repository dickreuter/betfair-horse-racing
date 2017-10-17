import bz2
import datetime
import logging
import os
from collections import defaultdict
from multiprocessing.pool import ThreadPool

import numpy as np
import requests

from betfair import Betfair
from betfair.constants import MarketProjection, OrderProjection
from betfair.models import MarketFilter, PriceProjection, LimitOrder, PlaceInstruction, TimeRange, ReplaceInstruction
# Start thread per horse race.
from horse_racing.legacy.backtesting.betf_race import BetFairRace
from horse_racing.utils.mongo_manager import MongoManager, Singleton
from horse_racing.utils.tools import get_config

log = logging.getLogger(__name__)
import numbers
import pandas as pd
import json

config = get_config()

tick_sizes = [(1.01, 2, 0.01),
              (2.02, 3, 0.02),
              (3.05, 4, 0.05),
              (4.1, 6, 0.1),
              (6.2, 10, 0.2),
              (10.5, 20, 0.5),
              (21, 30, 1.),
              (32, 50, 2.),
              (55, 100, 5.),
              (110, 1000, 10.)]


def create_ladder():
    return np.concatenate(list(map(lambda x: np.arange(*x), tick_sizes)))


def _split_list(to_split, step=5):
    for i in range(0, len(to_split), step):
        yield to_split[i:i + step]


price_ladder = create_ladder()


# Connect to BF.
# Find all horse races in UK.
# https://www.betfair.com/www/sports/exchange/readonly/v1/bymarket?_ak=nzIFcwyWhrlwYMrh&currencyCode=GBP&locale=en_GB&marketIds=1.138130951&rollupLimit=2&rollupModel=STAKE&types=MARKET_STATE,RUNNER_STATE,RUNNER_EXCHANGE_PRICES_BEST,RUNNER_DESCRIPTION


class Container(object, metaclass=Singleton):
    interested_types = ['WIN']
    refresh_interval = 1
    pre_match_interval = 30
    historic_data_url = r'https://historicdata.betfair.com/api/GetMyData'

    def __init__(self, sandbox_key=False):
        self.selected_events = {}
        self.markets = {}
        self.client = None
        self.sandbox_key = sandbox_key  # if true use sandbox,, if false use prod
        self.do_login()

    def do_login(self):
        __location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        username = config.get('Betfair', 'username')
        password = config.get('Betfair', 'password')
        certfile = config.get('Betfair', 'cert_file')
        devkey = config.get('Betfair', 'dev_app')
        prodkey = config.get('Betfair', 'prod_app')
        full_certfile = os.path.join(__location, certfile)

        self.client = Betfair(prodkey if not self.sandbox_key else devkey, full_certfile)
        self.client.login(username, password)

    def get_all_races(self):
        # Get all games, even those with no scores API feed, search 2 hours in the past
        delta = datetime.timedelta(seconds=60 * 70)
        to_time = datetime.datetime.now() + delta
        event_types = self.client.list_event_types(
            MarketFilter(text_query='horse')
        )
        horse_racing_id = event_types[0].event_type.id
        countries = config.get('Scraping', 'countries').split()
        events = self.client.list_events(filter=MarketFilter(event_type_ids=[horse_racing_id],
                                                             market_countries=countries,
                                                             market_start_time=TimeRange(to=to_time)))
        # market_type_codes=self.interested_types)
        if len(events) == 0:
            return [], []  # TODO: shouldn't these be returned as defaultdict?
        markets = defaultdict(list)
        for m in self.client.list_market_catalogue(MarketFilter(event_ids=[e.event.id for e in events],
                                                                market_start_time=TimeRange(to=to_time),
                                                                market_type_codes=self.interested_types),
                                                   market_projection=[MarketProjection['RUNNER_DESCRIPTION'],
                                                                      MarketProjection['EVENT'],
                                                                      MarketProjection['MARKET_DESCRIPTION'],
                                                                      MarketProjection['MARKET_START_TIME']
                                                                      ]):
            markets[m.event.id].append((m.market_id, m))
        return events, markets

    def get_single_race(self, market_id):
        events = self.client.list_events(filter=MarketFilter(market_ids=[market_id]))
        if len(events) == 0:
            return [], []  # TODO: shouldn't these be returned as defaultdict?
        markets = defaultdict(list)
        for m in self.client.list_market_catalogue(MarketFilter(market_ids=[market_id]),
                                                   market_projection=[MarketProjection['RUNNER_DESCRIPTION'],
                                                                      MarketProjection['EVENT'],
                                                                      MarketProjection['MARKET_DESCRIPTION'],
                                                                      MarketProjection['MARKET_START_TIME']
                                                                      ]):
            markets[m.event.id].append((m.market_id, m))
        return events, markets

    def update_markets(self, events, markets):
        pp = PriceProjection(price_data=['EX_BEST_OFFERS', 'EX_TRADED', 'SP_AVAILABLE', 'SP_TRADED'])
        market_ids = []
        for m in markets.values():
            for r in m:
                market_ids.append(r[0])
        markets_resp = []
        for market_list in _split_list(market_ids):
            markets_resp.extend(self.client.list_market_book(market_ids=market_list, price_projection=pp))
        return markets_resp

    def get_single_market(self, market_id):
        pp = PriceProjection(price_data=['EX_BEST_OFFERS', 'SP_AVAILABLE', 'SP_TRADED'])
        markets = self.client.list_market_book(market_ids=[market_id], price_projection=pp)
        return markets

    def place_limit_order(self, market, selection, stake, odds, side='BACK', persist='LAPSE', strategy=None):
        persist = config.getboolean("Betting", "persist")
        persist = 'LAPSE' if persist == False else 'PERSIST'
        bet = LimitOrder(size=max(2, stake) if side == 'BACK' else stake,  # stake is minimum 2 GBP
                         price=odds,
                         persistence_type=persist)
        order = PlaceInstruction(order_type='LIMIT',
                                 selection_id=int(selection),
                                 side=side,
                                 limit_order=bet)
        return self.client.place_orders(market, [order], customer_ref="MRE-{}-{}".format(market, selection),
                                        strategy_ref=strategy)

    def place_fill_or_kill(self, market, selection, stake, odds, side='BACK', strategy=None):
        bet = LimitOrder(size=max(2, stake) if side == 'BACK' else stake,
                         price=odds,
                         persistence_type='LAPSE',
                         time_in_force='FILL_OR_KILL',
                         min_fill_size=max(2, stake) if side == 'BACK' else stake)
        order = PlaceInstruction(order_type='LIMIT',
                                 selection_id=int(selection),
                                 side=side,
                                 limit_order=bet
                                 )
        return self.client.place_orders(market, [order], customer_ref="MRE-{}-{}".format(market, selection),
                                        strategy_ref=strategy)

    def welcome_message(self):
        acc = self.client.get_account_details()
        first_name = acc['first_name']
        acc = self.client.get_account_funds()
        funds = acc.available_to_bet_balance
        return "Welcome %s, your account balance is %s" % (first_name, funds)

    def get_open_orders(self):
        """
        Get current unfilled orders by market
        :return: dictionary of list of orders
        """
        projection = OrderProjection['EXECUTABLE']
        orders = self.client.list_current_orders(order_projection=projection)
        orders_by_market = defaultdict(list)
        for o in orders.current_orders:
            orders_by_market[o.market_id].append(o)
        return orders_by_market

    def replace_orders(self, market, bet_ids, new_prices):
        """
        Replace current orders with new prices
        :param market:
        :param bet_ids:
        :param new_prices:
        :return:
        """
        instructions = []
        for bet_id, np in zip(bet_ids, new_prices):
            instruction = ReplaceInstruction(bet_id=bet_id,
                                             new_price=np)
            instructions.append(instruction)
        return self.client.replace_orders(market_id=market, instructions=instructions)

    def get_cleared_orders(self, from_time=datetime.datetime.today() + datetime.timedelta(-1)):
        orders = self.client.list_cleared_orders(event_type_ids=[7],
                                                 bet_status='SETTLED',
                                                 settled_date_range=TimeRange(from_=from_time))
        trades_df = pd.DataFrame.from_records([x.values() for x in orders['cleared_orders']])
        total_commission = 0.
        if not trades_df.empty:
            trades_df.columns = orders['cleared_orders'][0].keys()
            total_commission_req = self.client.list_cleared_orders(event_type_ids=[7],
                                                                   bet_status='SETTLED',
                                                                   group_by='EVENT_TYPE',
                                                                   settled_date_range=TimeRange(from_=from_time))
            total_commission = total_commission_req['cleared_orders'][0].commission

        return trades_df, total_commission

    def get_account_balance(self):
        result = self.client.get_account_funds()
        return {k: result.get(k) for k in result.keys()}

    def get_race_status(self, events):
        results = self.client.list_race_details(events)
        if results:
            return pd.DataFrame.from_records([x.values() for x in results], columns=results[0].keys())

    def download_historic_data(self, start, end, countries=('GB', 'IE')):
        ssoid = self.client.session_token
        headers = {'ssoid': ssoid}
        d = {"sport": "Horse Racing",
             "plan": "Basic Plan",
             "fromDay": start.day,
             "fromMonth": start.month,
             "fromYear": start.year,
             "toDay": end.day,
             "toMonth": end.month,
             "toYear": end.year,
             "marketTypesCollection": ["WIN"],
             "countriesCollection": list(countries),
             "fileTypeCollection": ["M"]}
        response = requests.get('https://historicdata.betfair.com/api/DownloadListOfFiles', params=d, headers=headers)
        file_names = json.loads(response.text)
        races = []

        def inner(f):
            race_data = requests.get('http://historicdata.betfair.com/api/DownloadFile', params={'filePath': f},
                                     headers=headers)
            race_str = bz2.decompress(race_data.content).decode('utf8')
            return BetFairRace.create_from_json(race_str)

        pool = ThreadPool()
        for file in file_names:
            races.append(pool.apply_async(inner, args=tuple([file])))
        pool.close()
        pool.join()
        return [r.get() for r in races]


def place_bets(bets, selection_ids, prices, market_ids, event_id, race_start_time, container, armed=False,
               model_name=None, reference_price_for_initial_bet=0):
    log.info("Placing bets: {}".format(bets))
    horses = len(selection_ids)
    back_prices, lay_prices, back1, lay1, back2, lay2, ltp_prices = prices
    bets = bets[0:horses * 2]  # cut off padded horses
    log.info("len bets: {}".format(len(bets)))
    log.info("len selection_ids: {}".format(len(selection_ids)))
    unit_stake = config.getfloat("Betting", "stake")
    m = MongoManager()
    d = {}
    d['bets'] = bets
    d['selection_ids'] = selection_ids
    d['timestamp'] = datetime.datetime.now()
    d['armed'] = armed
    d['back_prices'] = back_prices.tolist()
    d['lay_prices'] = lay_prices.tolist()
    d['market_id'] = market_ids
    d['event_id'] = event_id
    d['ltps'] = ltp_prices.tolist()
    d['stake'] = float(unit_stake)

    # convert to datetime for mongodb saving
    if not type(race_start_time) == datetime.datetime:
        race_start_datetime = datetime.datetime.combine(datetime.date.today(), race_start_time)
    else:
        race_start_datetime = race_start_time
    d['race_start'] = race_start_datetime

    m.insert_document('place_bets', d, database='pnl')

    if armed:
        #
        # c = Container()
        for i, b in enumerate(bets):
            if not b:
                continue
            log.info("++++++++++++++++++++++++++++++++++++++++++++")
            bet_type = 'BACK' if i % 2 == 0 else 'LAY'
            price = back_prices[i // 2] if bet_type == 'BACK' else lay_prices[i // 2]

            ask_price = price
            stake = unit_stake

            if bet_type == 'LAY':
                price = lay_saftey_check(selection_id=selection_ids[i // 2],
                                         last_price=ltp_prices[i // 2],
                                         current_lay_price=price,
                                         best_back=back_prices[i // 2])

            theoretical_ltp_price = price
            # additional reducrion for early orders
            if reference_price_for_initial_bet == '0':
                log.info("Using ltp as reference")
            elif reference_price_for_initial_bet == '1':
                price = min(price, back_prices[i // 2]) if bet_type == 'LAY' else min(price, lay_prices[i // 2])
                log.info("Using level 1 as reference")
            elif reference_price_for_initial_bet == '2':
                price = min(price, back1[i // 2]) if bet_type == 'LAY' else min(price, lay1[i // 2])
                log.info("Using level2  as reference")
            elif reference_price_for_initial_bet == '3':
                price = min(price, back2[i // 2]) if bet_type == 'LAY' else min(price, lay2[i // 2])
                log.info("Using level3  as reference")
            else:
                log.error("Invalid value for reference_price_for_initial_bet")

            price = price_adjustment(price)



            log.info("Placing order on betfair: marketid: {}, selection: {}, price: {}".format(market_ids,
                                                                                               selection_ids[
                                                                                                   i // 2],
                                                                                               price))

            result = container.place_limit_order(market_ids, selection_ids[i // 2], stake, price,
                                                 side=bet_type,
                                                 strategy=model_name)

            try:
                m.insert_document('orders', {'market_id': market_ids,
                                             'event_id': event_id,
                                             'race_start': race_start_time,
                                             'selection': selection_ids[i // 2],
                                             'timestamp': datetime.datetime.now(),
                                             'stake': float(stake),
                                             'price': price,
                                             'theoretical_ltp_price': theoretical_ltp_price,
                                             'ltp': ltp_prices[i // 2],
                                             'original_ask_price': ask_price,
                                             'side': bet_type,
                                             'result': result.status,
                                             'error_code': result.error_code,
                                             'size_matched': result.instruction_reports[0].size_matched,
                                             'average_price_matched': result.instruction_reports[
                                                 0].average_price_matched,
                                             'betid': result.instruction_reports[0].bet_id,
                                             'model_name': model_name}, database='pnl')
            except:
                log.warning("inserting orders document failed, marketid: {}".format(market_ids))

            log.info("Result: {}, {}, matched {} on avg of {}".format(result.status,
                                                                             result.error_code,
                                                                             result.instruction_reports[0].
                                                                             size_matched,
                                                                             result.instruction_reports[0].
                                                                             average_price_matched))
            try:
                if result.status == "SUCCESS":
                    m.update_document('successful_bets',
                                      'market_id', market_ids,
                                      "successful_bets",
                                      selection_ids[i // 2],
                                      as_array=True)
            except:
                log.warning("Updating place_bets collection failed, marketid: {}".format(market_ids))

        return True


def lay_saftey_check(selection_id, last_price, current_lay_price, best_back):
    """ takes election ID and last scraped LTP as input, returns maximum lay """
    m = MongoManager()
    ltps = m.get_last_LTPs(selection_id, amount_of_prices=5)
    ltps.append(last_price)
    log.info("LTPs from db (not used): {}".format(ltps))

    try:

        # cap the value of the list to 500 and clean ltps from any erroneous/non-numerical value
        ltps = [min(x, 500) for x in ltps if isinstance(x, numbers.Number) and not np.isnan(x)]

        # take the median
        median = np.median(ltps)

    except:
        log.warning("Unable to calculate median from ltps: {}. Assigning a safety threshold".format(ltps))
        median = 500

    last_price_multiplier = config.getfloat("Restrictions", "last_price_multiplier")
    multiple_to_best_competitor = config.getfloat("Restrictions", "multiple_to_best_compatitor")
    absolute_maximum = config.getfloat("Restrictions", "absolute_maximum")

    max_lay = min(current_lay_price, absolute_maximum, last_price * last_price_multiplier, best_back * multiple_to_best_competitor)

    if max_lay < current_lay_price:
        log.warning("Restrict lay from {0} to {1}. | LTPs: {2} | best back: {3}".
                    format(current_lay_price, max_lay, ltps, best_back))

    log.info("current_lay_price (back level n for replacing_unfilled): {}".format(current_lay_price))
    log.info("LTP median (not used): {}".format(median))
    log.info("Last price (ltp or back): {}".format(last_price))
    log.info("best back (=best competitor): {}".format(best_back))

    return max_lay


def price_adjustment(price):
    i = 0
    while price_ladder[i] < price:
        i += 1
    return float(str(round(price_ladder[i], 2)))


if __name__ == '__main__':
    c = Container()
    r = c.download_historic_data(datetime.date(2018, 1, 1), datetime.date(2018, 1, 1))
    print(r)
