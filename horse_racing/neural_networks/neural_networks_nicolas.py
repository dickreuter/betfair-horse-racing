import logging
import os
import socket
import time
from datetime import datetime

import matplotlib
from keras.callbacks import TensorBoard, EarlyStopping

from horse_racing.neural_networks.custom_optimization import CustomPayoffs
from horse_racing.neural_networks.neural_network_base import NeuralNetworkBase
from horse_racing.utils.mongo_manager import MongoManager
from horse_racing.utils.tools import get_config

config = get_config()

if socket.gethostname() == config.get("Servers", "prod"):
    matplotlib.use('Agg')  # to work with linux, but will prevent showing plot in windows

import matplotlib.pyplot as plt
import numpy as np
from keras.layers import Dense, Dropout
from keras.models import Sequential
from keras.optimizers import Adam
from scipy.stats import ranksums
from sklearn.model_selection import KFold

dir_path = os.path.dirname(os.path.realpath(__file__))
path = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger(__name__)

features_per_horse = 60
force_horses_no = 44


class FlyingSpider(NeuralNetworkBase):

    def create_model(self, batchsize=False):
        optimal_lay = None

        total_result = []
        max_bs_list = []
        max_ls_list = []
        optimal_lay_list = []
        return_per_racehorse_list = []

        kf = KFold(n_splits=6, random_state=1, shuffle=True)

        n = 0
        for self.train_idx, self.test_idx in kf.split(range(len(self.X))):
            n += 1

            self.trainX = self.X[self.train_idx, :]
            self.trainY = self.Y[self.train_idx]
            self.train_payoff = self.Y[self.train_idx, 1].astype('float')
            self.testX = self.X[self.test_idx, :]
            self.testY = self.Y[self.test_idx]
            self.test_payoff = self.Y[self.test_idx, 1].astype('float')

            # self.weights = abs(self.weights_original[self.train_idx])

            # maximum number of hidden neurons to avoid overfitting
            # https://stats.stackexchange.com/questions/181/how-to-choose-the-number-of-hidden-layers-and-nodes-in-a-feedforward-neural-netw
            samples = self.trainX.shape[0]
            input_neurons = self.trainX.shape[1]
            output_neurons = 1
            alpha = 2
            max_hidden_neurons = 1000
            hidden_neurons = min(max_hidden_neurons, int(samples / (alpha * (input_neurons + output_neurons))))
            log.info("Hidden neurons: {}".format(hidden_neurons))

            self.normalize_data()

            epochs = 100
            # default batch size
            if not batchsize:
                batchsize = 1
            log.info("Start training with batch size: {}".format(batchsize))

            self.model = Sequential()
            self.model.add(Dense(hidden_neurons, activation='relu', input_shape=(input_neurons,)))
            self.model.add(Dropout(0.2))
            self.model.add(Dense(hidden_neurons, activation='relu', input_shape=(input_neurons,)))
            self.model.add(Dropout(0.2))
            self.model.add(Dense(output_neurons, activation='sigmoid'))

            self.model.compile(loss=self.cp.custom_cross_entropy,
                               optimizer=Adam(),
                               metrics=[self.cp.acc, self.cp.profit, self.cp.tp, self.cp.fp, self.cp.tn, self.cp.fn])

            timestr = time.strftime("%Y%m%d-%H%M%S") + "_" + str(n)
            self.tbCallBack = TensorBoard(log_dir='./Graph/{}'.format(timestr), histogram_freq=0, write_graph=True,
                                          write_images=False)

            self.early_stop = EarlyStopping(monitor='val_loss',
                                            min_delta=1e-7,
                                            patience=2,
                                            verbose=2, mode='auto')

            self.model.fit(self.trainX,
                           self.trainY,
                           validation_data=(self.testX, self.testY),
                           epochs=epochs,
                           batch_size=int(batchsize),
                           verbose=1,
                           callbacks=[self.tbCallBack, self.early_stop])

            scores = self.model.evaluate(self.testX, self.testY)
            log.info("\n%s: %.2f%%" % (self.model.metrics_names[1], scores[1] * 100))

            average_profit_per_bet, cumulative_returns, cumulative_all_in = \
                self.backtest(strategy=self.strategy)

            return_per_racehorse_list.append(average_profit_per_bet)
            total_result.append(average_profit_per_bet)
            plt.plot(cumulative_returns, label='strategy, kfold {}'.format(n))
            if self.strategy == 'lay':
                plt.plot(cumulative_all_in, 'b:', label='bet all, kfold {}'.format(n))
            plt.title("")
            plt.legend()

            if len(total_result) == 1 or average_profit_per_bet > max(total_result[:-1]):
                self.save_model()

        self.save_hyperparams(max_bs_list, max_ls_list, features_per_horse, batchsize,
                              return_per_racehorse_list, optimal_lay_list, self.norm)

        log.info("Mean of mean returns: {0:.2f}".format(np.mean(total_result)))

        ranksum_stat, p_stat = ranksums(total_result, np.zeros(len(total_result)))
        log.info("Statistically significantly different to zero p-value: {0:.2f}".format(p_stat))
        log.info("statistically significantly different to zero on 1% level: {}".format(p_stat < 0.01))
        log.info("statistically significantly different to zero on 5% level: {}".format(p_stat < 0.05))

        timestr = time.strftime("%Y%m%d-%H%M%S")
        plt.savefig(os.path.join(dir_path, 'plots/training-{}.png'.format(timestr)))

    def predict_one_sided(self, X, strategy):
        log.info("Starting tensorflow predict")
        X = self.normalize_data(prod_data=X)
        prediction = self.model.predict(X)
        log.info("Tensorflow predict completed")
        return prediction

    def predict(self, X):
        if X.shape[0] <= 3:
            log.info("3 or less valid horses. Not betting")
            return np.stack(([False] * X.shape[0], [False] * X.shape[0]), axis=-1).astype('bool')
        log.info("Starting tensorflow predict")
        X = self.normalize_data(prod_data=X)
        prediction = self.model.predict(X)
        log.info("Tensorflow predict completed")
        n = X.shape[0]
        back = np.array([False] * n).reshape(-1, 1)
        lay = np.round(prediction) > .5
        return np.stack((back, lay), axis=-1).astype('bool')


class FlyingSpiderBookie(FlyingSpider):
    def load_enriched_ts(self, from_year=2000, to_year=2100, strategy='back', clip=-200, localhost=True,
                         use_archive=False, countrycode=None):

        self.strategy = strategy

        m = MongoManager(use_remote=not localhost, use_archive=use_archive)

        log.info("Downloading...")
        df = m.download_enriched_TS(datetime(from_year, 1, 1, 0, 0), datetime(to_year, 12, 31, 23, 59),
                                    countrycode=countrycode, col='price_scrape_enriched_bookies')

        log.info("Loaded bets data: {}".format(len(df)))
        df = df.drop_duplicates(['marketid', 'selection_id'])
        df = df.sort_values('marketstarttime')
        log.info("After removing duplicates: {}".format(len(df)))

        if strategy == 'lay':
            df['act'] = 1 - df['winner']
        else:
            df['act'] = df['winner']

        self.X = df[['LTP t-0', 'average', 'minimum', 'maximum', 'median', 'std', 'participants', 'skew', 'kurtosis',
                     'overrun',
                     'ltp_bmp', 'mbp_overrun', 'vwap_ltp', 'ltp_bmp_median',
                     ]].values
        self.Y = df[['act', strategy]].values

        df['lay'] = df['lay'].clip(clip, 1)  # clip lays at clip value
        self.weights_original = df[strategy].values  # contains back or lay payoffs

        self.cp = CustomPayoffs(strategy)
