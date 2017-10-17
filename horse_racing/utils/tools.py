import os
import pickle
from configparser import ConfigParser
from itertools import accumulate, chain, repeat, tee
from os.path import abspath
from os.path import dirname

path = os.path.dirname(os.path.realpath(__file__))
config_filename = 'config.ini'


def get_dir(*folders):
    if folders[0] == 'codebase':
        return dirname(dirname(abspath(__file__)))


def get_config():
    config = ConfigParser()
    config.read(os.path.join(path, '..', config_filename))
    return config


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def load_object(filename):
    with open(filename, 'rb') as input:
        obj = pickle.load(input)
    return obj


def chunk(xs, n):
    assert n > 0
    L = len(xs)
    s, r = divmod(L, n)
    widths = chain(repeat(s + 1, r), repeat(s, n - r))
    offsets = accumulate(chain((0,), widths))
    b, e = tee(offsets)
    next(e)
    return [xs[s] for s in map(slice, b, e)]
