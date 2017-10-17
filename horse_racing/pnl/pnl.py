import logging
import socket
import sys
from datetime import timedelta, datetime

import matplotlib
from scipy.stats import ttest_ind
from tqdm import tqdm

from horse_racing.utils.tools import get_config, chunk

config = get_config()
if socket.gethostname() == config.get("Servers", "prod"):
    matplotlib.use('Agg')  # to work with linux, but will prevent showing plot in windows
from horse_racing.utils.mongo_manager import MongoManager
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from horse_racing.betfair_manager.engine import Container

log = logging.getLogger(__name__)


def propagate_race_results():
    log.info("Propagating race results")
    m = MongoManager()
    races = m.get_races_without_results()
    results = m.load_race_results([r['market_id'] for r in races])
    log.info("Found {} results".format(len(results)))

    for r in results:
        m.update_placed_bet_with_result(r['marketid'], r['winner'], r['losers'])


def propagate_race_results_to_price_scrape(col='price_scrape'):
    """ add winner and loser field to price_scrape collection"""
    m = MongoManager()
    from_date = datetime.now() - timedelta(days=30)
    log.info("Getting prices without race results since {}".format(from_date))
    races = m.get_price_scrape_without_results(from_date, col)
    log.info("Got {} races. Loading results and updating {} collection".format(len(races), col))
    if len(races) < 1:
        log.info("No races to process")
        return

    c = int(np.ceil(len(races) / 100))
    for race_chunk in tqdm(chunk(races, c)):
        results = m.load_race_results(race_chunk)

        if len(results) < 1:
            log.info("No results to process")
            continue

        for r in results:
            m.update_price_scrape_with_result(col, r['marketid'], r['winner'], r['losers'])


def eval_theoratical_pnl(args):
    log.info("Evaluating pnl")
    m = MongoManager()
    races = m.get_bets_to_calculate_pnl(overwrite_calculated_pnls=args['--overwrite_calculated_pnls'])

    for race in tqdm(races):
        back_pnl = [0]
        lay_pnl = [0]
        losers = race['losers']
        for i, horse in enumerate(race['selection_ids']):
            won = horse == race['winner']
            loser = horse in losers
            back_odds = race['ltps'][i]  # back_prices would understate the theoretical pnl
            lay_odds = race['ltps'][i]  # lay_prices would understate the theoretical pnl

            valid = 1 if lay_odds > 1 else 0  # exclude zero odds from theoretical pnl

            theoretical_pnl = [0]

            fees = config.getfloat("Betting", "fees")
            stake = float(race['stake'])
            if won and race['bets'][i * 2]:  # back on winner
                change = (back_odds * stake - stake) * (1 - fees)
                back_pnl.append(change * valid)
                theoretical_pnl.append(change * valid)
            if won and race['bets'][i * 2 + 1]:  # lay on winner
                change = -(lay_odds * stake - stake)
                lay_pnl.append(change * valid)
                theoretical_pnl.append(change * valid)
            if loser and race['bets'][i * 2]:  # back on loser
                change = -stake  # pylint: disable=E1130
                back_pnl.append(change * valid)
                theoretical_pnl.append(change * valid)
            if loser and race['bets'][i * 2 + 1]:  # lay on loser
                change = stake * (1 - fees)
                lay_pnl.append(change * valid)
                theoretical_pnl.append(change * valid)

            m.update_document2('orders', 'selection', horse,
                               'market_id', race['market_id'],
                               'theoretical_pnl', sum(theoretical_pnl))

            back_pnl_total = sum(back_pnl)
            lay_pnl_total = sum(lay_pnl)
            m.update_placed_bet_with_pnl(race['market_id'], back_pnl_total, lay_pnl_total)


def update_bets_with_settlement_from_betfair():
    log.info("Update bets with settlements from betfair")
    c = Container()
    settled_df, fees = c.get_cleared_orders()
    m = MongoManager()
    for index, row in settled_df.iterrows():
        m.update_orders(str(row['event_id']), row['selection_id'],
                        str(row['market_id']), 'SUCCESS',
                        row['price_matched'],
                        row['price_requested'], row['size_settled'], row['profit'])


def update_place_bets_from_orders():
    log.info("Update place_bets from orders collection")
    m = MongoManager()
    bf_profit = m.get_pnl_per_race_from_orders()

    for item in bf_profit:
        m.update_document(collection_name='place_bets',
                          id_name='market_id', id_value=item['_id'],
                          field_name='bf_profit', field_value=item['bf_profit'])


def list_all_bets():
    m = MongoManager()
    orders = m.get_all_orders()
    df = pd.DataFrame.from_dict(orders)
    df.fillna(value=0.0, inplace=True)
    log.info("Processing through orders: {}".format(len(df)))

    # Sanity Check
    if len(df) == 0:
        log.warning("No Pnl can be calculated as dataframe is empty")
        sys.exit()

    # Common variables
    fees = config.getfloat("Betting", "fees")
    x = np.array(range(len(df)))
    titles = ['bf_win', 'theoretical_win', 'bf_loss', 'theoretical_loss', 'price']
    xlabels = df['selection'].tolist()
    ylabels = ['Realized Profit', 'Theoretical Profit', 'Realized Loss', 'Theoretical Loss', 'Price']
    colors = ['r', 'g', 'r', 'g', 'b']
    dir_path = os.path.dirname(os.path.realpath(__file__))
    df['bf_win'] = df['bf_profit'].clip(lower=0) * (1 - fees)
    df['bf_loss'] = df['bf_profit'].clip(upper=0)
    df['theoretical_win'] = df['theoretical_pnl'].clip(lower=0)
    df['theoretical_loss'] = df['theoretical_pnl'].clip(upper=0)

    # PnL Plots Borders
    win_borders = None
    loss_borders = None
    if not np.all(np.isnan(df['bf_profit'])) and not np.all(np.isnan(df['theoretical_pnl'])):
        win_borders = [0, int(np.nanmax([np.nanmax(df['bf_win']), np.nanmax(df['theoretical_win'])]))]
        loss_borders = [int(np.nanmin([np.nanmin(df['bf_loss']), np.nanmin(df['theoretical_loss'])])), 0]

    # Plot Actual/Theoretical Wins
    # Overall View
    f, ax = plt.subplots()
    w = 0.3
    ax.bar(x, df['bf_win'], width=w, color='r', align='center')
    ax.bar(x + w, df['theoretical_win'], width=w, color='g', align='center')
    ax.autoscale(tight=True)
    ax.set_title('Wins in the last 24h')
    ax.set_ylabel('Profits')
    ax.minorticks_on()
    ax.set_xticks([])
    plt.setp(ax.get_xticklabels(), visible=False)
    plt.legend(['Realized', 'Theoretical'])
    if win_borders:
        ax.set_ylim([win_borders[0], 1.05 * win_borders[1]])
    plt.savefig(os.path.join(dir_path, '../static/orders_wins_overall.png'), dpi=180)

    # Individual View
    f, axs = plt.subplots(nrows=2)
    for i in range(0, 2):
        ax = axs[i]
        ax.bar(x, df[titles[i]], color=colors[i])
        ax.set_ylabel(ylabels[i])
        ax.minorticks_on()
        ax.set_xticks([])
        plt.setp(ax.get_xticklabels(), visible=False)
        if win_borders:
            ax.set_ylim([win_borders[0], 1.05 * win_borders[1]])
    axs[0].set_title('Wins in the last 24 hours')
    f.subplots_adjust(hspace=0)
    f.subplots_adjust(wspace=0)
    plt.savefig(os.path.join(dir_path, '../static/orders_wins.png'), dpi=180)

    # Plot Actual/Theoretical Losses
    # Overall View
    f, ax = plt.subplots()
    w = 0.6
    ax.bar(x, df['bf_loss'], width=w, color='r', align='center')
    ax.bar(x + w, df['theoretical_loss'], width=w, color='g', align='center')
    ax.autoscale(tight=True)

    ax.set_title('Losses in the last 24h')
    ax.set_ylabel('Losses')
    ax.minorticks_on()
    ax.set_xticks([])
    plt.setp(ax.get_xticklabels(), visible=False)
    plt.legend(['Realized', 'Theoretical'])
    if win_borders:
        ax.set_ylim([loss_borders[0] * 1.05, loss_borders[1]])
    plt.savefig(os.path.join(dir_path, '../static/orders_losses_overall.png'), dpi=180)

    # Individual View
    f, axs = plt.subplots(nrows=2)
    for i in range(0, 2):
        ax = axs[i]
        ax.bar(x, df[titles[i + 2]], color=colors[i + 2])
        ax.set_ylabel(ylabels[i + 2])
        ax.minorticks_on()
        ax.set_xticks([])
        plt.setp(ax.get_xticklabels(), visible=False)
        if loss_borders:
            ax.set_ylim([loss_borders[0] * 1.05, loss_borders[1]])
    f.subplots_adjust(hspace=0)
    f.subplots_adjust(wspace=0)
    plt.savefig(os.path.join(dir_path, '../static/orders_losses.png'), dpi=180)

    # Plot Bet Prices
    f, ax = plt.subplots()
    ax.bar(x, df[titles[-1]], color=colors[-1])
    ax.set_ylabel(ylabels[-1])
    ax.set_xlabel('Bets (Selection IDs)')
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(xlabels, rotation=90, fontsize=2)
    f.subplots_adjust(hspace=0)
    f.subplots_adjust(wspace=0)
    plt.savefig(os.path.join(dir_path, '../static/bets.png'), dpi=180)


def pnl_charts(start=0, end=0):
    log.info("Create charts")
    dir_path = os.path.dirname(os.path.realpath(__file__))
    m = MongoManager()

    # 24h bar chart
    data = m.get_all_pnl()
    df = pd.DataFrame(data)

    fees = config.getfloat("Betting", "fees")
    df.ix[df['bf_profit'] > 0] = df.ix[df['bf_profit'] > 0] * (1 - fees)

    if len(df) > 0:
        total_pnl = df['sum_total'].sum().round(1)
        total_back = df['sum_back'].sum().round(1)
        total_lay = df['sum_lay'].sum().round(1)
        bf_profit = df['bf_profit'].sum().round(1)

        ax = df.plot.bar()
        ax.set_title("Today's bets")
        ax.set_ylabel('Return')
        ax.set_xlabel('Races')
        ax.axhline(y=0, color='r', linestyle='-')
        # ax.text(0.5, -10, "Total PnL:  {}".format(total_pnl))
        # ax.text(0.5, -13, "Total Back: {}".format(total_back))
        # ax.text(0.5, -16, "Total Lay:  {}".format(total_lay))
        # ax.text(0.5, -19, "Total BF:  {}".format(bf_profit))
        dir_path = os.path.dirname(os.path.realpath(__file__))
        ax.get_figure().savefig(os.path.join(dir_path, '../static/chart.png'), dpi=180)

        # cumulative line chart
        df2 = df.cumsum()
        ax = df2.plot()
        ax.set_title('Horse racing return last 24h')
        ax.set_ylabel('Return')
        ax.set_xlabel('Races')
        ax.axhline(y=0, color='r', linestyle='-')
        dir_path = os.path.dirname(os.path.realpath(__file__))
        ax.get_figure().savefig(os.path.join(dir_path, '../static/chart_cumulative.png'), dpi=180)

    else:
        # create empty files

        log.warning("No bets in the last 24 hours")
        open(os.path.join(dir_path, '../static/chart.png'), 'w').close()
        open(os.path.join(dir_path, '../static/chart_cumulative.png'), 'w').close()

    # cumulative line chart since last year
    from_date = config.get("PNL", "from_date")
    from_date = datetime.strptime(from_date, "%Y-%m-%d")
    data = m.get_all_pnl(from_date)
    df = pd.DataFrame(data)

    ranksum_stat, p_stat = ttest_ind(df['bf_profit'].fillna(0).values, np.zeros(len(df['bf_profit'].values)))

    df = df.cumsum()
    ax = df.plot()
    balance_dict = get_account_balance()
    balance = balance_dict['available_to_bet_balance'] - balance_dict['exposure']
    ax.set_title("""Horse racing return last 365 days\np-stat: {:.2f} - {}\nCurrent Balance: {}""".
                 format(p_stat, p_stat < 0.05,
                        balance))
    ax.set_ylabel('Return')
    ax.set_xlabel('Races')

    ax.axhline(y=0, color='r', linestyle='-')
    ax.get_figure().savefig(os.path.join(dir_path, '../static/chart_cumulative_year.png'), dpi=180)


def send_summary_email(subject='PnL Report', text='PnL Report', attach_files=True):
    destination = config.get("Email", "destinations").split(',')

    me = email = config.get("Email", "login")
    password = config.get("Email", "password")

    POP3 = 'pop.gmx.com'
    SMTP = 'mail.gmx.com'

    # Create the container (outer) email message.
    msg = MIMEMultipart()
    msg['Subject'] = subject
    # me == the sender's email address
    # family = the list of all recipients' email addresses
    msg['From'] = email
    msg['To'] = ','.join(destination)
    msg.preamble = subject

    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText(text, 'html')
    msg.attach(msgText)

    # This example assumes the image is in the current directory

    if attach_files:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, '../static/chart.png'), 'rb') as fp:
            msgImage1 = MIMEImage(fp.read())
        with open(os.path.join(dir_path, '../static/chart_cumulative.png'), 'rb') as fp:
            msgImage2 = MIMEImage(fp.read())
        with open(os.path.join(dir_path, '../static/chart_cumulative_year.png'), 'rb') as fp:
            msgImage3 = MIMEImage(fp.read())
        with open(os.path.join(dir_path, '../static/bets.png'), 'rb') as fp:
            msgImage4 = MIMEImage(fp.read())

        # Define the image's ID as referenced above

        msg.attach(msgImage1)
        msg.attach(msgImage2)
        msg.attach(msgImage3)
        msg.attach(msgImage4)

    # Send the email via our own SMTP server.
    s = smtplib.SMTP(SMTP)
    s.starttls()
    s.login(email, password)

    s.sendmail(me, destination, msg.as_string())
    s.quit()


def get_account_balance():
    c = Container()
    return c.get_account_balance()


def get_days_trades():
    c = Container()
    return c.get_cleared_orders()
