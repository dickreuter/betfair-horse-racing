import numpy as np
import datetime
import json
import logging
import os
import socket
import time
from datetime import datetime
import matplotlib
import sys
from sklearn.preprocessing import MinMaxScaler

from horse_racing.utils.mongo_manager import MongoManager
from horse_racing.utils.tools import get_config
import matplotlib.pyplot as plt
from keras.losses import binary_crossentropy, mean_squared_error

from horse_racing.neural_networks.neural_networks_nicolas import FlyingSpider, FlyingSpiderBookie
from horse_racing.neural_networks.lay_all import LayAll

log = logging.getLogger('__name__')
dir_path = os.path.dirname(os.path.realpath(__file__))


def query_neural_network_for_bets(X):
    """ input X has to be a np array of shape [number_of_requested_predictions, elements]
    with ts starting at t-000.
    Returns betting recommendation in the form of bet,lay,bet,lay... as booleans in the same order as X
    Return shape for 2 bets and 44 horses would be (2,88)
    """
    config = get_config()
    nn_class = getattr(sys.modules[__name__], config.get('Betting', 'model_class'))
    n = nn_class()
    n.load_model()

    m = MongoManager()
    d = {}
    d['input'] = X.tolist()
    d['timestamp'] = datetime.now()
    predicted = (n.predict(X))
    d['output'] = predicted.tolist()
    log.info("Mean predicted profit across all bets: {}".format(np.mean(predicted)))
    if np.isnan(np.mean(predicted)):
        log.error("Tensorflow output: {}".format(predicted))
        log.error("Terminating thread")
        sys.exit()

    place_bet = predicted

    return place_bet, n.model_name


def train_ts(modelname, localhost=False, batchsize=False, from_year=2016, to_year=2016, strategy='lay',
             countrycode=None):
    nn_class = getattr(sys.modules[__name__], modelname)
    n = nn_class()

    n.load_enriched_ts(from_year=from_year, to_year=to_year, strategy=strategy, localhost=localhost,
                       countrycode=countrycode)
    n.create_model(batchsize=batchsize)


def backtest_ts(modelname, model_path, localhost, from_year, to_year, strategy='lay',
                scale_unfilled=1, scale_above_ltp=1, countrycode=None):
    nn_class = getattr(sys.modules[__name__], modelname)
    n = nn_class()

    n.load_enriched_ts(from_year=from_year, to_year=to_year, strategy=strategy, localhost=localhost,
                       countrycode=countrycode)
    n.load_model(model_path=model_path)

    # create an array with shape [races (this can be a single race), features_per_horse * horses, 1)
    n.testX = n.X
    n.testY = n.Y[:, 0]
    n.test_payoff = n.Y[:, 1]

    # scale negative payoffs
    n.test_payoff[n.test_payoff < 0] = n.test_payoff[n.test_payoff < 0] * scale_unfilled * scale_above_ltp
    n.test_payoff[n.test_payoff > 0] = n.test_payoff[n.test_payoff > 0] * scale_unfilled

    n.test_idx = range(n.testX.shape[0])

    n.normalize_data(skip_train=True)
    average_profit_per_bet, cumulative_returns, cumulative_all_in = n.backtest(strategy=strategy)
    plt.plot(cumulative_returns, 'r', label='strategy')
    if strategy == 'lay':
        plt.plot(cumulative_all_in, 'b:', label='place all')
    plt.legend()

    timestr = time.strftime("%Y%m%d-%H%M%S")
    plt.savefig(os.path.join(dir_path, 'plots/backtesting-{}.png'.format(timestr)))
