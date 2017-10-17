"""
Usage:
  app.py ts train STRATEGY CLASS COUNTRYCODES [--batchsize=<>] [--from_year=<>] [--to_year=<>] [--localhost]
  app.py ts backtest STRATEGY CLASS COUNTRYCODES [MODEL_PATH] [--from_year=<>] [--to_year=<>] [--localhost]
  app.py collect_prices
  app.py bet [--armed] [--sandbox_key] [--config=<>]
  app.py update_unfilled_orders [--armed] [--config=<>]
  app.py collect_results
  app.py evaluate_pnl [--overwrite_calculated_pnls] [--config=<>]
  app.py email_summary
  app.py upload_tarball FILE [DESTINATION]
  app.py map_reduce SOURCE DESTINATION CLASS [--localhost] [--use_archive]
  app.py propagate_race_results_to_price_scrape

Exmaple
  app.py ts train lay FlyingSpider GB,IE,US,NZ --localhost --from_year 2015 --to_year 2017
  app.py ts backtest lay FlyingSpider GB,IE,US,NZ --localhost --from_year 2016 --to_year 2016
  app.py propagate_race_results_to_price_scrape   adds a winner and losers column to each price in price_scrape
  app.py map_reduce price_scrape price_scrape_enriched DEBookies --localhost
"""

import logging
import socket
import sys
import traceback

import time
from datetime import datetime, timedelta

from docopt import docopt

hostname = socket.gethostname()


def log_except_hook(*exc_info):
    init_logger(screenlevel=logging.DEBUG, filename='uncaught_exceptions')
    log = logging.getLogger('horse_racing.app')
    text = "".join(traceback.format_exception(*exc_info))  # pylint: disable=E1120
    log.error("Unhandled exception: %s", text)

    if hostname == config.get("Servers", "prod"):
        from horse_racing.pnl.pnl import send_summary_email
        send_summary_email('uncaught exception alert', text, False)


sys.excepthook = log_except_hook


def check_for_available_race_and_bet(args):
    from horse_racing.utils.tools import get_config
    config = get_config()
    min_before_start = config.get("Betting", "min_before_start_initial_bet")
    reference_price_for_initial_bet = config.get("Betting", "reference_price_for_initial_bet")
    countrycodes = config.get('Betting', 'bet_countries').split()

    races_to_bet, selection_ids, market_ids, event_ids, race_start_times = \
        find_race_to_bet(min_before_start=int(min_before_start), countrycodes=countrycodes)

    wait_for_start = int(min_before_start) == 0
    if races_to_bet is not None:
        b = BetLogic()
        b.update_prices_and_place_bet(args,
                                      races_to_bet, selection_ids, market_ids, event_ids, race_start_times,
                                      wait_for_start, reference_price_for_initial_bet)


from horse_racing.utils import tools

args = docopt(__doc__)
if args['--config']:
    tools.config_filename = args['--config']

from horse_racing.utils.logger import init_logger
from horse_racing.utils.tools import get_config

config = get_config()

if args['ts']:
    init_logger(screenlevel=logging.INFO, filename='ts')  # set the log level for the screen output
    # only load later to avoid initialization time for tensorflow when not needed
    from horse_racing.neural_networks.neural_network_launcher import train_ts, backtest_ts

    if args['--from_year']:
        from_year = int(args['--from_year'])
    else:
        from_year = 2016
    if args['--to_year']:
        to_year = int(args['--to_year'])
    else:
        to_year = 2016

    if args['train']:
        train_ts(modelname=args['CLASS'],
                 localhost=args['--localhost'],
                 batchsize=args['--batchsize'],
                 from_year=from_year, to_year=to_year,
                 strategy=args['STRATEGY'],
                 countrycode=args['COUNTRYCODES'].split(','))

    if args['backtest']:
        default_modelpath = ''
        model_path = args['MODEL_PATH'] or default_modelpath
        backtest_ts(modelname=args['CLASS'], model_path=model_path,
                    localhost=args['--localhost'],
                    strategy=args['STRATEGY'],
                    from_year=from_year, to_year=to_year,
                    scale_unfilled=0.9,
                    scale_above_ltp=1.02,
                    countrycode=args['COUNTRYCODES'].split(','))

if args['collect_prices']:
    from horse_racing.scraping.price import collect_prices

    init_logger(screenlevel=logging.INFO, filename='collect_prices')

    # These are here now so we don't continuously reconnect when scraping ticks
    collect_prices()

    # continuous scraping for races starting soon

    from horse_racing.betfair_manager.query_market import find_race_to_bet

    cont_scraping_start = config.getint("Scraping", "cont_scraping_start")
    cont_scraping_end = config.getint("Scraping", "cont_scraping_end")
    cont_scraping_delay = config.getint("Scraping", "cont_scraping_delay")
    countrycodes = config.get('Scraping', 'cont_scraping_countries').split()
    _, _, market_ids, _, race_start_times = find_race_to_bet(min_before_start=int(cont_scraping_start),
                                                             countrycodes=countrycodes)

    if market_ids:
        init_logger(screenlevel=logging.INFO, filename='collect_prices_contd')
        while datetime.now() < race_start_times[0] + timedelta(minutes=cont_scraping_end):
            time.sleep(cont_scraping_delay)
            collect_prices(collection_name='price_scrape_tickdata', single_marketid=market_ids[0])

if args['bet']:
    init_logger(screenlevel=logging.DEBUG, filename='bet')
    from horse_racing.betfair_manager.bet_logic import BetLogic
    from horse_racing.betfair_manager.query_market import find_race_to_bet

    check_for_available_race_and_bet(args)

if args['update_unfilled_orders']:
    if config.getboolean("Betting", "update_unfilled_orders"):
        from horse_racing.betfair_manager.bet_logic import BetLogic

        init_logger(screenlevel=logging.DEBUG, filename='update_orders')
        b = BetLogic()
        b.update_placed_orders(args['--armed'])

if args['collect_results']:
    from horse_racing.scraping.price import collect_results

    init_logger(screenlevel=logging.DEBUG, filename='collect_results')
    collect_results()

if args['evaluate_pnl']:
    from horse_racing.pnl.pnl import eval_theoratical_pnl, pnl_charts, update_bets_with_settlement_from_betfair, \
        update_place_bets_from_orders, list_all_bets, propagate_race_results

    init_logger(screenlevel=logging.DEBUG, filename='evaluate_pnl')
    propagate_race_results()
    eval_theoratical_pnl(args)
    update_bets_with_settlement_from_betfair()
    update_place_bets_from_orders()
    list_all_bets()
    pnl_charts()

if args['email_summary']:
    from horse_racing.pnl.pnl import send_summary_email

    send_summary_email()

if args['upload_tarball']:
    from horse_racing.backtesting.historic_data_processor import TarLoader, DEBookies

    init_logger(screenlevel=logging.DEBUG, filename='upload_tarball')
    t = TarLoader()
    t.process_tar(args['FILE'])

    if args['DESTINATION']:
        col = args['DESTINATION']
    else:
        col = 'price_scrape_tarballs'
    t.save_races(col)

if args['map_reduce']:
    from horse_racing.backtesting.historic_data_processor import DEBookies, DEBase

    init_logger(screenlevel=logging.DEBUG, filename='map_reduce')

    de_class = getattr(sys.modules[__name__], args['CLASS'])
    de = de_class(args['SOURCE'], args['DESTINATION'], args['--localhost'], args['--use_archive'])
    de.map_reduce()

if args['propagate_race_results_to_price_scrape']:
    init_logger(screenlevel=logging.DEBUG, filename='propagate_race_results_to_price_scrape')
    from horse_racing.pnl.pnl import propagate_race_results_to_price_scrape

    propagate_race_results_to_price_scrape(col='price_scrape')
    propagate_race_results_to_price_scrape(col='price_scrape_tickdata')

# for all other modules just use log = logging.getLogger(__name__)
log = logging.getLogger('horse_racing.app')
log.info('job completed')
