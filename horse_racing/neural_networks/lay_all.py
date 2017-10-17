import logging
import os
import socket
import numpy as np
import pandas as pd

import matplotlib

from horse_racing.neural_networks.custom_optimization import CustomPayoffs
from horse_racing.neural_networks.neural_network_base import NeuralNetworkBase
from horse_racing.utils.mongo_manager import MongoManager
from horse_racing.utils.tools import get_config

config = get_config()

if socket.gethostname() == config.get("Servers", "prod"):
    matplotlib.use('Agg')  # to work with linux, but will prevent showing plot in windows

dir_path = os.path.dirname(os.path.realpath(__file__))
path = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger(__name__)


class LayAll(NeuralNetworkBase):

    def predict(self, X):
        n = X.shape[0]
        back = [False] * n
        lay = [True] * n
        return np.stack((back, lay), axis=-1)

    def predict_one_sided(self, X, strategy):
        n = X.shape[0]
        back = [False] * n
        lay = [True] * n
        if strategy=='lay':
            return np.array(lay)
        if strategy=='back':
            return np.array(back)

