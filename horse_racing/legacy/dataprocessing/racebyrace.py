import pandas as pd

from horse_racing.betfair_manager.utils import stones_to_lbs, fraction_to_decimal

nanos_to_days = (60. * 60 * 24 * 100000000)

def _modify_frame(h_df):
    h_df['LASTPOS'] = h_df['finpos'].shift(1)
    h_df['LASTRACE'] = h_df['RACEDATE'].rolling(2).apply(lambda x: x[1] - x[0])
    return h_df

def create_race_by_race(races, runners):
    # Create time since last race
    runners_and_riders = runners.merge(races, on='RACENUMBER')
    new_frames = []
    i =0
    runners_and_riders['RACEDATE'] = runners_and_riders['RACEDATE'] / nanos_to_days
    runners_and_riders['WEIGHT'] = runners_and_riders['WEIGHT'].apply(stones_to_lbs)
    runners_and_riders['NAME_C'] = runners_and_riders['NAME'].astype('category')
    runners_and_riders['ODDS'] = runners_and_riders['ODDS'].apply(fraction_to_decimal)
    grouped = runners_and_riders.groupby('NAME_C')
    print("Grouped")
    full_df = grouped.apply(_modify_frame)
    print("Applied")
    wanted_columns = ['RACENUMBER', 'NAME', 'HANDICAP', 'WEIGHT', 'DRAW', 'ODDS', 'LASTPOS', 'LASTRACE', 'finpos']
    #full_df['LASTRACE'] = full_df['LASTRACE'] / nanos_to_days
    #full_df['WEIGHT'] = full_df['WEIGHT'].apply(stones_to_lbs)
    return full_df[wanted_columns]

if __name__ == '__main__':
    store = pd.HDFStore(r'c:\Users\cms\Dropbox\Tennis Project\HorseRacing\srs.h5')
    race_by_race_df = create_race_by_race(store['frace'], store['frhorse'])
    store['frace_by_race'] = race_by_race_df