import pandas as pd
import numpy as np
import sklearn as sk
import json
import os
import sys
import time
from horse_racing.utils.mongo_manager import MongoManager
from datetime import datetime

# Retrieve/aggregate data
path = "C:\\Users\\Claudio\\Dropbox\\Tennis Project\\HorseRacing\\"
columns_all = ['RACEDATE', 'COURSE', 'GOINGSTRING', 'DISTANCE', 'RACECLASS', 'RACETYPE', 'RACEVALUE', 'runcount_1', 'wincount_1', 'winners_1', 'HANDICAP_1', 'WEIGHT_1', 'DRAW_1', 'ODDS_1', 'runcount_2', 'wincount_2', 'winners_2', 'HANDICAP_2', 'WEIGHT_2', 'DRAW_2', 'ODDS_2', 'WINNER']
track_cols = ['RACEDATE', 'COURSE', 'GOINGSTRING', 'DISTANCE', 'RACECLASS', 'RACETYPE', 'RACEVALUE']
store = pd.HDFStore(path + 'srs.h5')
h2h = store['h2h-hr']
winners = store['h2hwinners-hr']
h2h['WINNER'] = winners # Complete Dataset with winner results as "WINNER" column
h2h.columns = columns_all

# Divide Training/Test Datasets
cutoff_date = int(time.mktime(datetime(2017, 1, 1).timetuple()))
h2h_train = h2h[h2h['RACEDATE'] < cutoff_date]
h2h_test = h2h[h2h['RACEDATE'] >= cutoff_date]

# Reduced Dataset without track-specific details (to be incorporated later)
h2h_red = h2h.drop(track_cols, axis=1)
h2h_train_red = h2h_train.drop(track_cols, axis=1)
h2h_test_red = h2h_test.drop(track_cols, axis=1)

# Save data as json
json.dump(h2h.to_json(orient='index'), open(path + 'h2h.json', 'wb'))
json.dump(h2h_train.to_json(orient='index'), open(path + 'h2h_train.json', 'wb'))
json.dump(h2h_test.to_json(orient='index'), open(path + 'h2h_test.json', 'wb'))
json.dump(h2h_red.to_json(orient='index'), open(path + 'h2h_red.json', 'wb'))
json.dump(h2h_train_red.to_json(orient='index'), open(path + 'h2h_train_red.json', 'wb'))
json.dump(h2h_test_red.to_json(orient='index'), open(path + 'h2h_test_red.json', 'wb'))

# Upload data into MongoDB
client = MongoManager()
client.upload_dataframe(h2h, 'h2h')
client.upload_dataframe(h2h_red, 'h2h_red')

#----------#
# ANALYSIS #
#----------#
training_set = h2h_train_red.values
test_set = h2h_test_red.values

# NOW LET'S HAVE FUN!
