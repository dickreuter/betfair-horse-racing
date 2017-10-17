import json
import logging
import os
import socket
import time
from datetime import datetime

import matplotlib
from scipy.stats import ranksums
from sklearn.preprocessing import MinMaxScaler

from horse_racing.neural_networks.custom_optimization import CustomPayoffs
from horse_racing.utils.mongo_manager import MongoManager
from horse_racing.utils.tools import get_config

config = get_config()

if socket.gethostname() == config.get("Servers", "prod"):
    matplotlib.use('Agg')  # to work with linux, but will prevent showing plot in windows

import numpy as np
from keras.callbacks import TensorBoard
from keras.models import model_from_json

dir_path = os.path.dirname(os.path.realpath(__file__))
path = os.path.dirname(os.path.realpath(__file__))
log = logging.getLogger(__name__)

features_per_horse = 60
force_horses_no = 44


class NeuralNetworkBase():
    def __init__(self):
        self.optimal_lay = None  # optimal limit for maximum lay
        self.X = None
        self.Y = None
        self.testX = None
        self.testY = None
        self.trainX = None
        self.trainY = None
        self.winning_lays_risk = None
        self.train_idx = None
        self.test_idx = None
        self.norm = None
        self.train_payoff = None
        self.test_payoff = None

        timestr = time.strftime("%Y%m%d-%H%M%S")
        self.tbCallBack = TensorBoard(log_dir='./Graph/{}'.format(timestr), histogram_freq=0, write_graph=True,
                                      write_images=False)

    def load_enriched_ts(self, from_year=2000, to_year=2100, strategy='back', clip=-200, localhost=True,
                         use_archive=True, countrycode=None):
        self.strategy = strategy

        m = MongoManager(use_remote=not localhost, use_archive=use_archive)

        log.info("Downloading...")
        df = m.download_enriched_TS(datetime(from_year, 1, 1, 0, 0), datetime(to_year, 12, 31, 23, 59),
                                    countrycode=countrycode)
        log.info("Loaded bets data: {}".format(len(df)))
        df = df.drop_duplicates(['marketid', 'selection_id'])
        df = df.sort_values('marketstarttime')

        log.info("After removing duplicates: {}".format(len(df)))

        if strategy == 'lay':
            df['act'] = 1 - df['winner']
        else:
            df['act'] = df['winner']

        self.X = df[['LTP t-0', 'average', 'minimum', 'maximum', 'median', 'std', 'participants', 'skew', 'kurtosis',
                     'overrun']].values
        self.Y = df[['act', strategy]].values

        df['lay'] = df['lay'].clip(clip, 1)  # clip lays at clip value
        self.weights_original = df[strategy].values  # contains back or lay payoffs

        self.cp = CustomPayoffs(strategy)

    def load_model(self, model_path=None):
        # load json and create model
        if model_path == None:
            model_path = config.get("Betting", "default_model_path")
        self.model_name = os.path.basename(model_path)  # For putting in the strategy ref
        log.info("Loading model from path: {}".format(model_path))

        json_file = open(os.path.join(path, model_path, 'model.json'), 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        self.model = model_from_json(loaded_model_json)
        # load weights into new model
        self.model.load_weights(os.path.join(path, model_path, 'model.h5'))

        with open(os.path.join(path, model_path, 'hyperparams.json')) as f:
            d = json.load(f)

        self.optimal_lay = 1000  # np.min(d['optimal_lay'])

        try:
            self.norm = d['norm']
            self.norm['x_scale'] = np.array(self.norm['x_scale'])
            self.norm['x_min'] = np.array(self.norm['x_min'])
        except KeyError:
            log.info("No normalization info in loaded model")

    def create_model(self):
        raise NotImplementedError("To be implemented by subclass")

    def predict(self, X):
        log.info("Starting tensorflow predict")
        prediction = self.model.predict(X)
        log.info("Tensorflow predict completed")
        return prediction

    def predict_one_sided(self, X, strategy):
        raise NotImplementedError("To be implemented by subclass for training and backtesting back and lay separately")

    def normalize_data(self, skip_train=False, prod_data=None):
        self.scaler_x = MinMaxScaler(feature_range=(0, 1))

        if self.norm == None:
            self.scaler_x.fit(self.X)
            self.norm = {'x_scale': self.scaler_x.scale_, 'x_min': self.scaler_x.min_}

        else:
            self.scaler_x.scale_ = self.norm['x_scale']
            self.scaler_x.min_ = self.norm['x_min']
        if prod_data is None:
            if not skip_train:
                self.trainX = self.scaler_x.transform(self.trainX)
            self.testX = self.scaler_x.transform(self.testX)
        else:
            return self.scaler_x.transform(prod_data)

    def save_model(self):
        with open(path + "/model.json", "w") as json_file:
            json_file.write(self.model.to_json())
        self.model.save_weights(path + "/model.h5")

    def save_hyperparams(self, max_bs_list, max_ls_list, features_per_horse, batchsize,
                         return_per_racehorse, optimal_lay, norm):
        d = {}
        d['max_bs_list'] = max_bs_list
        d['max_ls_list'] = max_ls_list
        d['features_per_horse'] = features_per_horse
        d['batchsize'] = batchsize
        d['return_per_racehorse'] = return_per_racehorse
        d['optimal_lay'] = optimal_lay

        norm['x_scale'] = norm['x_scale'].tolist()
        norm['x_min'] = norm['x_min'].tolist()
        d['norm'] = norm

        with open(path + "/hyperparams.json", "w") as fp:
            json.dump(d, fp)

    def backtest(self, use_test_sample=True, predicted=False, strategy='lay'):
        X = self.testX if use_test_sample else self.trainX
        Y = self.testY if use_test_sample else self.trainY
        payoffs = self.test_payoff.astype('float') if use_test_sample else self.train_payoff.astype('float')

        idx = self.test_idx if use_test_sample else self.train_idx

        log.debug("Query neural network for predictions. Total number of bets: {}".format(Y.shape[0]))
        if type(predicted) != np.ndarray:
            predicted = (self.predict_one_sided(X, strategy))

        place_bet = predicted
        # calculate the risk on lays to see where the lay profit comes from and filter out bets higher than max_lay

        # risk_stake = (place_bet * self.winning_lays_risk[idx])
        # max_lay_restriction_array = risk_stake > -max_lay

        # lay_limit_filter = np.stack((np.ones(len(max_lay_restriction_array)), max_lay_restriction_array), axis=1)
        # place_bet = place_bet * lay_limit_filter

        # if strategy == 'lay':
        #     place_bet = place_bet[1::2]
        # elif strategy == 'back':
        #     place_bet = place_bet[0::2]

        # multiply with non-normalized original data to get actual profits
        profit_strategy = (place_bet.round().flatten() * payoffs).astype('float')

        average_strategy = np.average(profit_strategy.astype('float'))
        average_all_in = np.average(payoffs)

        profit_strategy_sum = np.sum(profit_strategy)
        profit_all_in_sum = np.sum(payoffs)

        cumulative_returns = np.cumsum(profit_strategy)
        cumulative_all_in = np.cumsum(payoffs)

        std_dev = np.std(profit_strategy)
        std_dev_all = np.std(payoffs)

        max_drawdown_strategy = np.min(profit_strategy)
        max_drawdown__all = np.min(payoffs)

        sharpe_ratio_strategy = profit_strategy_sum / std_dev
        sharpe_ratio_all_in = profit_all_in_sum / std_dev_all

        log.info("Total profit: £{0:.2f}".format(profit_strategy_sum))
        log.info("Total profit: all in £{0:.2f}".format(profit_all_in_sum))

        log.info("std dev strategy: {0:.4f}".format(std_dev))
        log.info("std dev all in {0:.4f}".format(std_dev_all))

        log.info("max drawdown strategy: {0:.2f}".format(max_drawdown_strategy))
        log.info("max drawdown all in {0:.2f}".format(max_drawdown__all))

        # return_per_race = np.sum(profit_per_game) / len(profit_per_game)

        log.info("Avg profit per bet: £{0:.3f}".format(average_strategy))
        log.info("Avg profit all in: £{0:.3f}".format(average_all_in))
        # log.info("Avg amount of horses per race: {0:.2f}".format(np.average(np.sum(self.horse_valid, axis=1))))

        bet = place_bet.round().flatten()
        avg_bet = np.average(bet)
        log.info("Fraction of bets placed per total bets: {0:.3f}".format(avg_bet))
        log.info("total placed bets: {0:}".format(np.sum(bet)))

        log.info("of total # of possible bets: {}".format(predicted.shape[0]))

        ranksum_stat, p_stat = ranksums(profit_strategy.flatten(), np.zeros(len(profit_strategy.flatten())))
        log.info("Statistically significantly different to zero p-value: {0:.4f}".format(p_stat))
        log.info("statistically significantly different to zero on 1% level: {}".format(p_stat < 0.01))
        log.info("statistically significantly different to zero on 5% level: {}".format(p_stat < 0.05))
        return average_strategy, cumulative_returns, cumulative_all_in
