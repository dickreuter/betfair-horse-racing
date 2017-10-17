from sklearn.preprocessing import LabelBinarizer
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

from horse_racing.utils.mongo_manager import MongoManager
from sklearn.model_selection import train_test_split
from sklearn.ensemble import AdaBoostClassifier
import pandas as pd
import numpy as np


def find_outliers():
    m= MongoManager()
    prices = m.mongodb.price_scrape.find({'selection_id': 7767293})
    price_df = pd.DataFrame.from_records(prices)
    pass

def get_classifier_df():
    m = MongoManager()
    results = m.mongodb.price_scrape.find(({'countrycode' : { '$in' : ['GB', 'IE']}, 'seconds_until_start' : { '$lt': 60}}))
    records = []
    keys = ['LTP', 'VWAP', 'back_prices0', 'back_sizes0', 'eventid' ,'lay_prices0', 'lay_sizes0', 'marketid',
            'max_bookie_price', 'mean_bookie_price', 'median_bookie_price', 'min_bookie_price', 'selection_id',
            'total_matched']
    for r in results:
        record = { k:v for k,v in r.items() if k in keys}
        records.append(record)
    df = pd.DataFrame.from_records(records)
    results = m.mongodb.results_scrape.find({'marketid' : {'$in' : [ x for x in df['marketid'].values]}})
    race_records = []
    for r in results:
        record = { (r['marketid'], r['winner'] ): 'WIN'}
        for l in r['losers']:
            record[(r['marketid'], l)] = 'LOSE'
        race_records.append(record)
    race_results=pd.concat([pd.Series(x) for x in race_records])
    race_results.name = 'outcome'
    df =df.set_index(['marketid', 'selection_id'])
    race_results.index.names  = df.index.names
    df=df.join(race_results).dropna()
    # df[(df['back_prob'] - df['bookie_prob']) > 0.025]
    df['back_prob'] = 1/ df['back_prices0']
    df['lay_prob'] = 1/ df['lay_prices0']
    df['bookie_prob'] = 1/df['median_bookie_price']
    df['vwap_prob'] = 1/df['VWAP']
    df['ltp_prob'] = 1/df['LTP']
    return df

def prepare_model_inputs(input_df, model_klass=LinearSVC):
    wanted_columns = ['back_prob', 'bookie_prob', 'ltp_prob', 'lay_prob']
    X = input_df[wanted_columns].values
    lb = LabelBinarizer()
    Y = lb.fit_transform(df['outcome'])
    X_train , X_test, Y_train, Y_test = train_test_split(X,Y, test_size=0.2)
    kf = StratifiedKFold(n_splits=3)
    model = model_klass()
    model.fit(X_train, Y_train)
    print(model.score(X_test, Y_test))
    predictions = model.predict(X_test)
    print("Total backs made: %s" %  np.bincount(predictions)[1])
    bet_df = pd.DataFrame(X_test)
    bet_df['results'] = Y_test.T[0]
    bet_df['predictions'] = predictions
    winners_df = bet_df[predictions.astype(bool)]
    winners_df['price'] = 1/winners_df[0]
    points = winners_df[winners_df['results']==1]['price'].sum()
    print("points: {}".format(points-winners_df.shape[0]))


def get_data(countries, extra_columns=True):
    m = MongoManager()
    results = m.mongodb.price_scrape.find(({'countrycode' : { '$in' : ['GB', 'IE', 'US', 'AU']}, 'max_bookie_price' : { '$exists' : True}, 'seconds_until_start' : { '$lt': 60}}))
    records = []
    keys = ['LTP', 'VWAP', 'back_prices0', 'back_sizes0', 'eventid' ,'lay_prices0', 'lay_sizes0', 'marketid']
    if extra_columns:
        keys.extend(['max_bookie_price', 'mean_bookie_price', 'median_bookie_price', 'min_bookie_price', 'selection_id',
            'total_matched', 'far_price', 'near_price'])
    for r in results:
        record = { k:v for k,v in r.items() if k in keys}
        records.append(record)
    df = pd.DataFrame.from_records(records)
    results = m.mongodb.results_scrape.find({'marketid' : {'$in' : [ x for x in df['marketid'].values]}})
    race_records = []
    for r in results:
        record = { (r['marketid'], r['winner'] ): 'WIN'}
        for l in r['losers']:
            record[(r['marketid'], l)] = 'LOSE'
        race_records.append(record)
    race_results=pd.concat([pd.Series(x) for x in race_records])
    race_results.name = 'outcome'
    df =df.set_index(['marketid', 'selection_id'])
    race_results.index.names  = df.index.names
    #df=df.join(race_results).dropna()
    return df.join(race_results)

def get_starting_prices():
    df = get_data(['GB','IE'])
    # df[(df['back_prob'] - df['bookie_prob']) > 0.025]
    df['back_prob'] = 1/ df['back_prices0']
    df['bookie_prob'] = 1/df['median_bookie_price']
    df['vwap_prob'] = 1/df['VWAP']
    total = 0
    for _,r in df[(df['back_prob'] - df['bookie_prob']) > 0.025].iterrows():
        if r['outcome'] == 'WIN':
            total += r['back_prices0'] - 1
        else:
            total -= 1
    print("Backing @ bf_price with 2.5% delta: {}".format(total))

    df.to_csv('/Users/richardjeffries/sample.csv')

if __name__=='__main__':
    df = get_classifier_df()
    #prepare_model_inputs(df, model_klass=AdaBoostClassifier)
    get_starting_prices()