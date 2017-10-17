import logging
import math
import sys
import time

import numpy as np
import pandas as pd

from horse_racing.betfair_manager.engine import place_bets, Container, price_adjustment, lay_saftey_check
from horse_racing.utils.mongo_manager import MongoManager
from horse_racing.utils.tools import get_config

log = logging.getLogger(__name__)


class BetLogic():

    def __init__(self):
        self.container = Container()

    def update_prices_and_place_bet(self, args, races_to_bet, selection_ids, market_ids, event_ids, race_start_times,
                                    wait_for_start=True, reference_price_for_initial_bet=0):
        log.info("---calling update_prices_and_place_bet---")
        log.info("market_ids: {}".format(market_ids))
        log.info("event_ids: {}".format(event_ids))
        log.info("race_start_times: {}".format(race_start_times))

        # Spin until horses are 'going behind'
        race_id = '{}.{}'.format(event_ids[0], race_start_times[0].strftime('%H%M'))  # TODO add market time.
        race_status = self.container.get_race_status(event_ids)
        log.debug("race_status: {}".format(race_status))
        if race_status[race_status['race_id'].astype(str) == race_id].empty:
            log.debug("Race status for market_id {} not available, getting new prices immediately".
                      format(market_ids[0]))
            new_prices = self.container.get_single_market(market_ids[0])
        else:
            current_status = race_status[race_status['race_id'] == race_id]['race_status'].values[0]
            n = 0
            while current_status not in ('ATTHEPOST', 'GOINGBEHIND'):
                if not wait_for_start:
                    break
                n += 1
                if n > 180:
                    sys.exit()
                log.info("current_status: {} - {}".format(current_status, n))
                time.sleep(10)
                status_df = self.container.get_race_status(event_ids)
                current_status = status_df[status_df['race_id'] == race_id]['race_status'].values[0]
                if current_status in ['OFF', 'RESULT', 'FINISHED', 'FINALRESULT', 'RACEVOID', 'NORACE',
                                      'MEETINGABANDONED',
                                      'RERUN', 'ABANDONED', 'WEIGHEDIN']:
                    log.warning("Missed race: {}, race status became {}".format(market_ids[0],
                                                                                current_status))
                    return
            log.debug("Race status changed to {} for market_id {}, getting new prices")
            new_prices = self.container.get_single_market(market_ids[0])

        # This is all just in case the selection ids are not the same as the model inputs
        new_selection_ids = [r.selection_id for r in new_prices[0].runners]

        # todo: this block needs to be put into a function with fallback logic and return results
        # ============
        best_backs = [(r.ex.available_to_back[0].price if len(r.ex.available_to_back) else 0) for r in
                      new_prices[0].runners]
        best_lays = [(r.ex.available_to_lay[0].price if len(r.ex.available_to_lay) else 0) for r in
                     new_prices[0].runners]
        try:
            best_backs1 = [(r.ex.available_to_back[1].price if len(r.ex.available_to_back) else 0) for r in
                           new_prices[0].runners]
        except IndexError:
            best_backs1 = best_backs

        try:
            best_lays1 = [(r.ex.available_to_lay[1].price if len(r.ex.available_to_lay) else 0) for r in
                          new_prices[0].runners]
        except IndexError:
            best_lays1 = best_lays

        try:
            best_backs2 = [(r.ex.available_to_back[2].price if len(r.ex.available_to_back) else 0) for r in
                           new_prices[0].runners]
        except IndexError:
            best_backs2 = best_backs1

        try:
            best_lays2 = [(r.ex.available_to_lay[2].price if len(r.ex.available_to_lay) else 0) for r in
                          new_prices[0].runners]
        except IndexError:
            best_lays2 = best_lays1

        ltps = [r.last_price_traded for r in new_prices[0].runners]

        log.info("new_prices (before fillna): {}".format(ltps))

        best_back_series = pd.Series(data=best_backs, index=new_selection_ids).fillna(0)
        best_lay_series = pd.Series(data=best_lays, index=new_selection_ids).fillna(0)
        best_back1_series = pd.Series(data=best_backs1, index=new_selection_ids).fillna(0)
        best_lay1_series = pd.Series(data=best_lays1, index=new_selection_ids).fillna(0)
        best_back2_series = pd.Series(data=best_backs2, index=new_selection_ids).fillna(0)
        best_lay2_series = pd.Series(data=best_lays2, index=new_selection_ids).fillna(0)

        ltps_series = pd.Series(data=ltps, index=new_selection_ids).fillna(0)
        # ============

        # recreate np array from flattened list of list
        try:
            races_to_bet_back = np.array(races_to_bet[0]).reshape(len(selection_ids[0]), -1)
            races_to_bet_lay = np.array(races_to_bet[0]).reshape(len(selection_ids[0]), -1)

            # Create a series just in case the order of runners is different
            races_to_bet_back[:, 0] = ltps_series[selection_ids[0]].values.reshape(len(selection_ids[0]))
            races_to_bet_lay[:, 0] = ltps_series[selection_ids[0]].values.reshape(len(selection_ids[0]))
        except ValueError:
            log.error("Some of the horses have no historic data. SelectionIDs: {}, races to bet: {}".
                      format(len(selection_ids[0]), len(races_to_bet[0])))

        # TODO: Check if races_to_bet_lay contains only 1st column of valid values and all 0s otherwise

        # get neural network prediction: the result is equivalent as calling the function twice

        # filter out horses that don't run
        valid = ltps_series > 0
        ltps = ltps_series[valid]
        selection_ids = np.array(new_selection_ids)[valid].tolist()

        l = np.sum(valid)

        average = [ltps_series[valid].mean()] * l
        minimum = [ltps_series[valid].min()] * l
        maximum = [ltps_series[valid].max()] * l
        median = [ltps_series[valid].median()] * l
        std = [ltps_series[valid].std()] * l
        skew = [ltps_series[valid].skew()] * l
        kurtosis = [ltps_series[valid].kurtosis()] * l
        participants = [l] * l
        overrun = [(1 / ltps_series[valid]).sum()] * l

        input = pd.DataFrame({"00": ltps,
                              "01": average,
                              "02": minimum,
                              "03": maximum,
                              "04": median,
                              "05": std,
                              "06": participants,
                              "07": skew,
                              "08": kurtosis,
                              "09": overrun}).values

        log.info("Tensorflow input array: {}".format(input))
        from horse_racing.neural_networks.neural_network_launcher import query_neural_network_for_bets
        log.info("selection_ids: {}".format(selection_ids))
        log.info("ltp series:")
        log.info(ltps_series)
        recommendations, model_name = query_neural_network_for_bets(input)

        # stitch together the two results into one, using the part of both that is relevant
        # (back RESULTS FROM the first [0, ::2] and lay for the second [1, 1::2])
        bets = recommendations.flatten()

        place_bets(bets.tolist(), selection_ids, (best_back_series[selection_ids].values,
                                                  best_lay_series[selection_ids].values,
                                                  best_back1_series[selection_ids].values,
                                                  best_lay1_series[selection_ids].values,
                                                  best_back2_series[selection_ids].values,
                                                  best_lay2_series[selection_ids].values,

                                                  ltps_series[selection_ids].values),
                   market_ids[0], event_ids[0],
                   race_start_times[0],
                   self.container, args['--armed'],
                   model_name,
                   reference_price_for_initial_bet)

    def update_placed_orders(self, armed=False):
        config = get_config()
        m = MongoManager()

        open_orders = self.container.get_open_orders()

        use_level = config.get("Betting", "use_level").split(',')
        # minutes_to_start
        if len(open_orders) > 0:
            log.info("Currently open order: {}".format(len(open_orders)))
        for market, orders in open_orders.items():
            log.info("Updating order for market: {}".format(market))
            new_prices = self.container.get_single_market(market)
            updated_prices = []
            updated_betids = []
            for o in orders:
                selection_id = o.selection_id
                secs_to_start = m.get_secs_to_start(market)
                log.info("Seconds to start: {}".format(secs_to_start))
                if not secs_to_start or secs_to_start < \
                        -config.getint("Betting", "update_until_secs_after_start"):  # pylint: disable=E1130
                    log.info("Ignoring order\n----------------")
                    continue
                log.info("Selection ID: {}".format(selection_id))
                ltp_price = 0
                lays = [0, 0, 0]
                backs = [0, 0, 0]
                for r in new_prices[0].runners:
                    if r.selection_id != selection_id:
                        continue
                    backs = [r.ex.available_to_back[x].price for x in range(len(r.ex.available_to_back))]
                    lays = [r.ex.available_to_lay[x].price for x in range(len(r.ex.available_to_lay))]
                    ltp_price = r.last_price_traded
                log.info("New backs: {}".format(backs))
                log.info("New lays: {}".format(lays))
                min_to_start = math.floor(secs_to_start / 60)
                log.info("Minutes until start: {}".format(min_to_start))
                try:
                    level_at_minutes_to_start = int(use_level[min_to_start])
                    log.info("Using Level: {}".format(level_at_minutes_to_start))
                except IndexError:
                    log.info("use_level not set for {} minutes to start. Aborting".format(min_to_start))
                    return

                level_at_minutes_to_start = min(level_at_minutes_to_start, len(backs) + 1)
                log.info("Final level to use: {}".format(level_at_minutes_to_start))
                new_price = ltp_price if level_at_minutes_to_start == 0 else backs[level_at_minutes_to_start - 1]

                log.info("Updating to new price: {}".format(new_price))
                new_price = lay_saftey_check(selection_id=o.selection_id,
                                             last_price=ltp_price,
                                             current_lay_price=new_price,
                                             best_back=backs[0])
                new_price = price_adjustment(new_price)
                updated_betids.append(o.bet_id)
                updated_prices.append(new_price)
                if armed:
                    m.update_order_price(o.market_id, o.selection_id, o.bet_id, min_to_start, new_price)

            if len(updated_betids) > 0:
                log.info("Updated bet_ids: {}".format(updated_betids))
                log.info("Updated prices: {}".format(updated_prices))
                if armed:
                    self.container.replace_orders(market, updated_betids, updated_prices)
