import bz2
import datetime as dt
import logging
import tarfile

import numpy as np
import pandas as pd
from tqdm import tqdm

from horse_racing.legacy.backtesting.betf_race import BetFairRace
from horse_racing.utils.mongo_manager import MongoManager
from horse_racing.utils.tools import get_config, chunk

log = logging.getLogger(__name__)


class TarLoader():
    def process_tar(self, file):
        self.races = []
        tf = tarfile.open(file)
        for m in tqdm(tf.getmembers()):
            self.races.append(TarLoader.create_race(tf.extractfile(m).read()))

    def save_races(self, col):
        m = MongoManager(use_archive=True, use_remote=False)
        for race in tqdm(self.races):
            out = []
            d = {}
            d['winner'] = 'na'
            d['losers'] = []

            for k, v in race.runners.items():
                if v.status == 'LOSER':
                    d['losers'].append(k)
                elif v.status == 'WINNER':
                    d['winner'] = k
            df = race.get_odds_dataframe(False)
            selection_ids = df.columns
            # df['overrun_at_start'] = sum(1 / race.get_starting_prices())
            df['countrycode'] = race.countryCode
            df['marketstarttime'] = race.marketTime
            df['marketid'] = race.marketId
            df['marketstarttime'] = df['marketstarttime'].values.astype('datetime64[s]')

            for selection_id in selection_ids:
                df_new = df[[selection_id, 'marketstarttime', 'countrycode', 'marketid']].reset_index()
                df_new.columns = ['timestamp', 'LTP', 'marketstarttime', 'countrycode', 'marketid']
                df_new['timestamp'] = df_new['timestamp'].values.astype('datetime64[s]')
                df_new['selection_id'] = selection_id
                df_new['seconds_until_start'] = df_new['marketstarttime'] - df_new['timestamp']
                df_new['seconds_until_start'] = df_new['seconds_until_start'].astype('timedelta64[s]')
                if selection_id == d['winner']:
                    df_new['winner'] = True
                else:
                    df_new['winner'] = False
                if selection_id in d['losers']:
                    df_new['loser'] = True
                else:
                    df_new['loser'] = False

                df_new = df_new[df_new['seconds_until_start'] < 70 * 60]

                if not d['winner'] == 'na':  # only races that have a winner
                    dirty = df_new.to_dict(orient='records')
                    clean = [x for x in dirty if type(x['LTP'] == float) and x['LTP'] > 1]  # remove nan and 0 LTPs
                    out.extend(clean)

            if len(out) > 0:
                m.insert_list_of_documents(col, out)

    @staticmethod
    def create_race(data):
        race_data = bz2.decompress(data).decode('utf8')
        race = BetFairRace.create_from_json(race_data)
        return race


class DEBase():
    def __init__(self, source, destination, use_local, use_archive):
        log.info("source {}".format(source))
        log.info("destination {}".format(destination))
        log.info("use_local {}".format(use_local))
        log.info("use_archive_db {}".format(use_archive))

        self.use_archive_db = use_archive
        self.m = MongoManager(use_remote=not use_local, use_archive=use_archive)
        self.source_collection = source
        self.destination_collection = destination

    def map_reduce(self, has_bookie=False):
        # check for latest entry in historical database
        # self.last_datetime = self.m.get_latest_date_in_enriched_prices(self.destination_collection)
        # if not self.last_datetime:
        self.last_datetime = dt.datetime(2018, 1, 1)

        log.info("Get available marketids")
        new_marketids = self.m.get_distinct('marketid',
                                            self.source_collection,
                                            self.last_datetime,
                                            must_have_bookie=has_bookie)
        log.info("got {}".format(len(new_marketids)))

        log.info("Get marketids already in enriched database")
        already_available_markeids = self.m.get_distinct('marketid',
                                                         self.destination_collection,
                                                         self.last_datetime,
                                                         must_have_bookie=False)
        log.info("got {}".format(len(already_available_markeids)))

        marketids_to_collect = list(new_marketids - already_available_markeids)

        log.info("Start download from date: {}".format(self.last_datetime))
        log.info("Download new marketids to enrich in chunks. Total marketids to process: {}".format(len(marketids_to_collect)))

        # set to higher value if larger amount needs to be processed simulataneiously, but if keys
        # are missing at certain time periods (such as mean_bookie_price t-0) the whole batch will be ignored

        batchsize = 1

        c = int(np.ceil(len(marketids_to_collect) / batchsize))

        for marketids in tqdm(chunk(marketids_to_collect, c)):
            self.historicals = self.m.download_raw_prices(self.last_datetime,
                                                          marketids,
                                                          self.source_collection,
                                                          max_rows=999999999,
                                                          has_bookie=has_bookie)

            self.df = pd.DataFrame.from_dict(self.historicals)
            del self.historicals
            l=len(self.df)
            if l==0:
                # log.warning("No new races found that match the criteria in current chunk")
                continue
            else:
                log.info("Total bets enriching: {}".format(l))

            try:
                self.unstack_timeseries_to_closest_minutes()
            except ValueError:
                continue
                # log.warning("error")

            try:
                self.calculate_metrics()
            except KeyError:
                log.warning("Key Error.  Ignoring the whole batch. Make sure batch size is 1.")
                continue

            self.calculate_payoffs()
            self.output_formatting()

            db = 'archive' if self.use_archive_db else 'price'
            self.df['timestamp'] = dt.datetime.now()
            self.m.upload_dataframe(self.df, self.destination_collection, db)

    def unstack_timeseries_to_closest_minutes(self, fields_to_stack=['LTP']):
        """ convert the times to an index t-000, t-001, t-002..."""
        self.df['minutes_to_start'] = 't-' + np.floor(self.df['seconds_until_start'] / 60).astype('int').astype('str')
        fields_to_stack.extend(['countrycode', 'loser', 'marketid', 'marketstarttime',
                                'selection_id', 'winner',
                                'minutes_to_start'])
        self.df = self.df[fields_to_stack]
        self.df = self.df.sort_values('minutes_to_start', ascending=False)
        self.df = self.df.drop_duplicates(['selection_id', 'marketid', 'minutes_to_start'], keep='last')
        self.df = self.df.set_index(['marketid', 'selection_id', 'countrycode', 'loser', 'marketstarttime',
                                     'winner', 'minutes_to_start'])
        self.df = self.df.unstack(level=6).reset_index()
        self.df.columns = [' '.join(col).strip() for col in self.df.columns.values]

    def calculate_metrics(self):
        """ stack timeseries and horses along columns in multi index dataframe """
        self.df['LTP'] = self.df['LTP t-0']
        self.df['horse'] = self.df.groupby('marketid').cumcount()  # add horse number in each group
        self.df_indexed = self.df.set_index(['marketid', 'horse'])

        log.info("Calculating 1d metrics")
        average = self.df_indexed['LTP'].mean(axis=0, level=0).to_frame().reset_index()
        average.columns = ['marketid', 'average']
        minimum = self.df_indexed['LTP'].min(axis=0, level=0).to_frame().reset_index()
        minimum.columns = ['marketid', 'minimum']
        maximum = self.df_indexed['LTP'].max(axis=0, level=0).to_frame().reset_index()
        maximum.columns = ['marketid', 'maximum']
        median = self.df_indexed['LTP'].median(axis=0, level=0).to_frame().reset_index()
        median.columns = ['marketid', 'median']
        std = self.df_indexed['LTP'].std(axis=0, level=0).to_frame().reset_index()
        std.columns = ['marketid', 'std']
        participants = self.df_indexed.count(level=0)['winner'].to_frame().reset_index()
        participants.columns = ['marketid', 'participants']
        skew = self.df_indexed['LTP'].skew(axis=0, level=0).to_frame().reset_index()
        skew.columns = ['marketid', 'skew']
        kurtosis = self.df_indexed['LTP'].kurtosis(axis=0, level=0).to_frame().reset_index()
        kurtosis.columns = ['marketid', 'kurtosis']
        overrun = (1 / self.df_indexed['LTP']).sum(axis=0, level=0).to_frame().reset_index()
        overrun.columns = ['marketid', 'overrun']

        # stat metrics of historical elements
        log.info("Calculating 2d metrics")
        all_price_headings = ['LTP t-' + str(i) for i in range(60)]

        log.info("Calculating average_2d")
        average_2d = self.df_indexed[all_price_headings].stack().mean(level=0).to_frame().reset_index()
        average_2d.columns = ['marketid', 'average_2d']

        log.info("Calculating min_2d")
        min_2d = self.df_indexed[all_price_headings].stack().min(level=0).to_frame().reset_index()
        min_2d.columns = ['marketid', 'min_2d']

        log.info("Calculating max_2d")
        max_2d = self.df_indexed[all_price_headings].stack().max(level=0).to_frame().reset_index()
        max_2d.columns = ['marketid', 'max_2d']

        log.info("Calculating median_2d")
        median_2d = self.df_indexed[all_price_headings].stack().median(level=0).to_frame().reset_index()
        median_2d.columns = ['marketid', 'median_2d']

        log.info("Calculating std_2d")
        std_2d = self.df_indexed[all_price_headings].stack().std(level=0).to_frame().reset_index()
        std_2d.columns = ['marketid', 'std_2d']

        log.info("Calculating skew_2d")
        skew_2d = self.df_indexed[all_price_headings].stack().skew(level=0).to_frame().reset_index()
        skew_2d.columns = ['marketid', 'skew_2d']

        log.info("Calculating kurtosis_2d")
        kurtosis_2d = self.df_indexed[all_price_headings].stack().kurtosis(level=0).to_frame().reset_index()

        kurtosis_2d.columns = ['marketid', 'kurtosis_2d']

        log.info("Merging 1d metrics")
        self.df = self.df.merge(average, on='marketid')
        self.df = self.df.merge(minimum, on='marketid')
        self.df = self.df.merge(maximum, on='marketid')
        self.df = self.df.merge(median, on='marketid')
        self.df = self.df.merge(std, on='marketid')
        self.df = self.df.merge(participants, on='marketid')
        self.df = self.df.merge(skew, on='marketid')
        self.df = self.df.merge(kurtosis, on='marketid')
        self.df = self.df.merge(overrun, on='marketid')

        log.info("Merging 2d metrics")
        self.df = self.df.merge(average_2d, on='marketid')
        self.df = self.df.merge(min_2d, on='marketid')
        self.df = self.df.merge(max_2d, on='marketid')
        self.df = self.df.merge(median_2d, on='marketid')
        self.df = self.df.merge(std_2d, on='marketid')
        self.df = self.df.merge(skew_2d, on='marketid')
        self.df = self.df.merge(kurtosis_2d, on='marketid')

    def calculate_payoffs(self):
        self.df = self.df.fillna(0)
        config = get_config()
        fees = config.getfloat("Betting", "fees")
        stake = 1  # hard coded for training for comparison purposes

        """ Creates X and Y in assigning the payoff to Y by removing the winner column from original df """

        payoff_back = np.where(self.df['winner'].values,
                               (stake * self.df['LTP'].values - stake) * (1 - fees),  # back winner
                               -np.ones((self.df['LTP'].values.shape)) * stake)  # back loser
        payoff_back = np.where(self.df['winner'] != -1, payoff_back, 0)  # replace na with 0 payoff

        # payoff when lay: -odds when win, 1 when loss
        payoff_lay = np.where(self.df['winner'].values,
                              -(stake * self.df['LTP'].values - stake),  # lay winner
                              stake * np.ones((self.df['LTP'].values.shape)) * (1 - fees))  # lay loser
        payoff_lay = np.where(self.df['winner'] != -1, payoff_lay, 0)  # replace na with 0 payoff

        # keep the lay odds to analyse the potential risk on the lays we bet on
        winning_lay_risk = np.minimum((self.df['LTP'].values - 1) * (-1), np.zeros(payoff_lay.shape))

        self.df['back'] = payoff_back
        self.df['lay'] = payoff_lay
        self.df['lay_risk'] = winning_lay_risk

    def output_formatting(self):
        self.df = self.df[[
            'marketstarttime', 'countrycode', 'marketid', 'selection_id',

            'LTP t-0', 'LTP t-7', 'average', 'minimum', 'maximum', 'median', 'std', 'participants', 'skew', 'kurtosis',
            'average_2d', 'min_2d', 'max_2d', 'median_2d', 'std_2d', 'skew_2d', 'kurtosis_2d',
            'overrun',

            'winner', 'back', 'lay', 'lay_risk'
        ]]
        self.df = self.df.drop_duplicates(['marketid', 'selection_id'])


class DEBookies(DEBase):
    def __init__(self, source, destination, use_local, use_archive):
        super().__init__(source, destination, use_local, use_archive)

    def unstack_timeseries_to_closest_minutes(self):
        fields_to_stack = ['LTP', 'mean_bookie_price','median_bookie_price', 'VWAP', 'bookies']
        super().unstack_timeseries_to_closest_minutes(fields_to_stack)

    def map_reduce(self, has_bookie=True):
        super().map_reduce(has_bookie=has_bookie)

    def calculate_metrics(self):
        self.df['MBP'] = self.df['mean_bookie_price t-0']
        self.df['vwap_ltp'] = self.df['VWAP t-0'] / self.df['LTP t-0']
        self.df['ltp_bmp'] = self.df['LTP t-0'] / self.df['mean_bookie_price t-0']
        self.df['ltp_vwap'] = self.df['LTP t-0'] / self.df['VWAP t-0']
        self.df['ltp_bmp_median'] = self.df['LTP t-0'] / self.df['median_bookie_price t-0']
        # self.df['ltp_matchbook'] = self.df['LTP t-0'] / self.df['bookies t-0'].apply(lambda d: [for x['price'] in d if x['name']=='matchbook'][0])
        super().calculate_metrics()

        mbp_overrun = (1 / self.df_indexed['MBP']).sum(axis=0, level=0).to_frame().reset_index()
        mbp_overrun.columns = ['marketid', 'mbp_overrun']
        self.df = self.df.merge(mbp_overrun, on='marketid')

    def output_formatting(self):
        self.df = self.df[[
            'marketstarttime', 'countrycode', 'marketid', 'selection_id',

            'LTP t-0', 'LTP t-7', 'average', 'minimum', 'maximum', 'median', 'std', 'participants', 'skew', 'kurtosis',
            'average_2d', 'min_2d', 'max_2d', 'median_2d', 'std_2d', 'skew_2d', 'kurtosis_2d',
            'overrun',
            'ltp_bmp', 'mbp_overrun', 'vwap_ltp', 'ltp_bmp_median',

            'winner', 'back', 'lay', 'lay_risk'
        ]]
        self.df = self.df.drop_duplicates(['marketid', 'selection_id'])


def de_duplicate():
    m = MongoManager(use_remote=False, use_archive=True)
    df = m.get_dataframe("price_scrape_enriched2")
    df = df.drop_duplicates(['marketid', 'selection_id'])
    m.upload_dataframe(df, "price_scrape_enriched_deduplicated")

# if __name__ == '__main__':
#     de_duplicate()
