import os
import random

import pandas as pd
from file_read_backwards import FileReadBackwards
from flask import Flask, render_template

from horse_racing.betfair_manager.engine import Container
from horse_racing.pnl.pnl import get_account_balance, get_days_trades
from horse_racing.utils.mongo_manager import MongoManager

app = Flask(__name__)


@app.route('/')
def index():
    rnd = random.randint(1, 999999)

    return render_template('index.html', rnd=str(rnd))


@app.route('/logging')
def logging():
    def get_logfile(filename):
        try:
            log_temp = []
            with FileReadBackwards(os.path.join(os.path.dirname(__file__), 'log', filename + '.log'),
                                   encoding='utf-8') as f:
                for l in f:
                    log_temp.append(l + "\n")
                log = ''.join(log_temp)
        except:
            log = ''
        return log

    bet = get_logfile('bet')
    bet_errors = get_logfile('bet_errors')
    collect_prices = get_logfile('collect_prices')
    collect_prices_contd = get_logfile('collect_prices_contd')
    collect_prices_contd_errors = get_logfile('collect_prices_contd_errors')
    collect_prices_errors = get_logfile('collect_prices_errors')
    update_orders = get_logfile('update_orders')
    update_orders_errors = get_logfile('update_orders_errors')
    uncaught_exceptions = get_logfile('uncaught_exceptions')

    return render_template('logging.html',
                           bet=bet,
                           bet_errors=bet_errors,
                           collect_prices=collect_prices,
                           collect_prices_errors=collect_prices_errors,
                           collect_prices_contd=collect_prices_contd,
                           collect_prices_contd_errors=collect_prices_contd_errors,
                           update_orders=update_orders,
                           update_orders_errors=update_orders_errors,
                           uncaught_exceptions=uncaught_exceptions,
                           rnd=str(random.randint(1, 999999)))


@app.route('/pnl_summary')
def pnl_summary():
    m = MongoManager()
    titles = ['']
    tables = []

    c = Container()
    c.do_login()  # for re-login to avoid timeouts

    titles.append('PnL Summary from Betfair')
    tables.append(pd.DataFrame(get_account_balance(), index=[0]).to_html(index=False))

    trades_df, commission = get_days_trades()
    summary = {"Total trades": trades_df.shape[0],
               "Number of Races": len(trades_df['market_id'].unique()),
               "Median Lay": trades_df[trades_df['side'] == 'LAY']['price_matched'].median(),
               "Median Back": trades_df[trades_df['side'] == 'BACK']['price_matched'].median(),
               "Profit per bet": trades_df['profit'].sum() / trades_df.shape[0],
               "Total Profit": trades_df['profit'].sum(),
               "Commission charged": commission,
               "Real PnL": trades_df['profit'].sum() - commission
               }

    titles.append('Order summary from Betfair')
    tables.append(pd.DataFrame(summary, index=[0]).to_html(index=False))

    titles.append('Latest trades (source: orders collection)')
    m = MongoManager()
    orders = m.get_all_orders()
    df = pd.DataFrame.from_dict(orders)
    df.sort_values(by=['timestamp'], inplace=True, ascending=False)
    tables.append(df[['bf_profit', 'theoretical_pnl', 'average_price_matched', 'bf_price_matched', 'bf_price_matched',
                      'ltp', 'original_ask_price', 'price', 'result', 'market_id', 'selection', 'timestamp',
                      'race_start']].to_html())

    settled_df, fees = c.get_cleared_orders()
    titles.append('Settled trades (source: Betfair)')
    tables.append(settled_df[['event_id', 'market_id', 'selection_id',
                              'bet_id', 'placed_date', 'persistence_type', 'order_type', 'side',
                              'price_requested', 'settled_date', 'bet_count',
                              'price_matched', 'price_reduced', 'size_settled',
                              'profit']].to_html())

    titles.append('Unmatched trades (orders collection with missing betfair pnl)')
    unfilled_orders = m.get_unfilled_orders()
    unfilled_orders_df = pd.DataFrame.from_dict(unfilled_orders)
    tables.append(unfilled_orders_df.to_html())

    return render_template('table.html', tables=tables, titles=titles, fees=fees)


@app.route('/upcoming')
def upcoming_races():
    m = MongoManager()
    tables = []
    titles = ['', 'Upcoming races']
    df = pd.DataFrame.from_dict(m.upcoming_races())
    tables.append(df.to_html())
    return render_template('table.html', tables=tables, titles=titles)


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
