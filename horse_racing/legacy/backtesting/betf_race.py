import json
import pandas as pd
import datetime

import pytz


class Runner(object):

    def __init__(self, runner_def):
        for k,v in runner_def.items():
            self.__dict__[k] = v
        self.ts = []
        self.ltps = []
        #self.model_date = pd.DataFrame()

    def update_runner(self, update):
        for k,v in update.items():
            self.__dict__[k] = v

    @staticmethod
    def from_dict(new_dict):
        r = Runner(new_dict)
        r = Runner(new_dict)
        r.ts = new_dict['ts']
        r.ltps = new_dict['ltps']
        return r

class BetFairRace(object):

    def __init__(self):
        self.runners = {}
        self.marketTime = None

    def set_runners(self, runners):
        for r in runners:
            try:
                self.runners[r['id']].update_runner(r)
            except KeyError:
                self.runners[r['id']] = Runner(r)

    def set_market_defintion(self, definition):
        for k,v in definition.items():
            if k == 'runners':
                self.set_runners(v)
            else:
                self.__dict__[k] = v

    def update_runners(self, r, timestamp):
        runner = self.runners[r['id']]
        runner.ltps.append(r['ltp'])
        runner.ts.append(timestamp)

    def get_odds_dataframe(self, names=True):
        ts_dict = {}
        for r,rd in self.runners.items():
            if len(rd.ts)<1:
                continue # skip horses with no values in ts
            ts_dict[r if not names else rd.name] = pd.Series(rd.ltps,index=map(lambda x: datetime.datetime.fromtimestamp(x/1000,tz=pytz.UTC), rd.ts))
        return pd.DataFrame.from_dict(ts_dict).fillna(method='ffill')

    def get_prerace_odds_dataframe(self, names=True):
        odds_df = self.get_odds_dataframe(names)
        ms = datetime.datetime.strptime(self.marketTime, '%Y-%m-%dT%H:%M:%S.%fZ')
        return odds_df[odds_df.index < ms]

    def get_winner(self, name=True):
        for k,v in self.runners.items():
            if v.status == 'WINNER':
                return v.name if name else k

    def get_starting_prices(self, name=True):
        race_start_time = datetime.datetime.strptime(self.marketTime, "%Y-%m-%dT%H:%M:%S.%fZ")
        odds_df = self.get_odds_dataframe(names=name)
        return odds_df.iloc[odds_df.index.get_loc(race_start_time, method='pad')]

    def get_favourite(self, name=True):
        return self.get_starting_prices(name=name).idxmin()

    def get_hours_before(self, name=True, hours=1):
        race_start_time = datetime.datetime.strptime(self.marketTime, "%Y-%m-%dT%H:%M:%S.%fZ")
        odds_df = self.get_odds_dataframe(names=name)
        slice_begin = race_start_time+datetime.timedelta(hours=hours*-1)
        return odds_df.iloc[odds_df.index.get_loc(slice_begin, method='pad'):odds_df.index.get_loc(race_start_time, method='pad')]

    def get_fixed_points(self, points=(1,3,5), names=True):
        mt = datetime.datetime.strptime(self.marketTime, "%Y-%m-%dT%H:%M:%S.%fZ")
        odds_df = self.get_odds_dataframe(names)
        return odds_df.iloc[[odds_df.index.get_loc(mt - datetime.timedelta(minutes=m), method='pad') for m in points]]

    @staticmethod
    def create_from_json(json_strings):
        bfr = BetFairRace()
        #json_strings = bz2.decompress(bytes(bz2_data)).decode('utf-8')
        for s in json_strings.split('\n'):
            try:
                data = json.loads(s)
            except:
                pass
            timestamp = data['pt']
            for r in data['mc']:
                if 'marketDefinition' in r.keys():
                    # market definition
                    bfr.set_market_defintion(r['marketDefinition'])
                if 'id' in r.keys():
                    bfr.marketId = r['id']
                if 'rc' in r.keys():
                    # Runner change
                    for s in r['rc']:
                        bfr.update_runners(s, timestamp)
        return bfr

    def to_json(self):
        new_dict = {}
        for k,v in self.__dict__.items():
            if k == 'runners':
                runner_list = []
                for i, r in v.items():
                    runner_list.append( r.__dict__)
                new_dict[k] = runner_list
            else:
                new_dict[k] = v
        return json.dumps(new_dict)

    def to_dict(self):
        return json.loads(self.to_json())


    @staticmethod
    def from_json(json_data):
        new_dict = json.loads(json_data)
        bfr=BetFairRace()
        for k,v in new_dict.items():
            if k == 'runners':
                for r in v:
                    bfr.runners[r['id']]=Runner.from_dict(r)
            elif k =='id':
                bfr.__dict__['marketId'] = v
            else:
                bfr.__dict__[k] = v
        return bfr