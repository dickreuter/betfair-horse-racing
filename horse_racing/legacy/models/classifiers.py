import sklearn
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import AdaBoostClassifier
import pandas as pd
import numpy as np

from horse_racing.legacy.models.model_config import training_epoch, number_of_records

full_data_columns = ['COURSE', 'GOINGSTRING', 'DISTANCE', 'RACECLASS',
       'RACEVALUE', 'runcount_1', 'wincount_1', 'winners_1',
       'HANDICAP_1', 'WEIGHT_1', 'runcount_2',
       'wincount_2', 'winners_2', 'HANDICAP_2', 'WEIGHT_2',
       'ODDS_2', 'ODDS_1', 'RACETYPE']
data_columns = ['GOINGSTRING', 'DISTANCE', 'HANDICAP_1', 'WEIGHT_1', 'HANDICAP_2', 'WEIGHT_2',
       'ODDS_1', 'ODDS_2']

#'RACETYPE'

def prepare_data(input, output):
    to_remove = input['RACEDATE'] < training_epoch
    input = input[to_remove]
    output = output[to_remove]
    input = input[data_columns]
    for l in [ 'COURSE', 'GOINGSTRING', 'RACECLASS']:
        le = sklearn.preprocessing.LabelEncoder()
        try:
            le.fit(input[l])
            input[l]=le.transform(input[l])
        except KeyError:
            continue
    X = sklearn.preprocessing.scale(input.values)
    elms = np.arange(X.shape[0])
    np.random.shuffle(elms)
    index = elms[:number_of_records]
    Y = output
    return X[index], Y[index].values

# Adaboost ~ 66%
# Randomforest ~ 62%
# SVC ~65%
# Decision tree ~ 57% [gives almost equal importance]
# KNeighbors ~ 59%
# Gaussian Naive - 60%

def train_and_test(X,y, model=AdaBoostClassifier):
    skf = StratifiedKFold(n_splits=5)
    skf.get_n_splits(X, y)
    for train_index, test_index in skf.split(X, y):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        rcf = model()
        rcf.fit(X_train, y_train)
        #print(rcf.feature_importances_)
        print(rcf.score(X_test, y_test))

if __name__ =='__main__':
    store = pd.HDFStore(r'c:\Users\cms\Dropbox\Tennis Project\HorseRacing\srs.h5')
    h2h = store['h2h-hr']
    winners = store['h2hwinners-hr']
    X,Y = prepare_data(h2h, winners)
    train_and_test(X,Y)