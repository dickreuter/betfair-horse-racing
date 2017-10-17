import itertools
import pandas as pd
import numpy as np
import time

from horse_racing.betfair_manager.utils import distance_to_yards, stones_to_lbs, fraction_to_decimal

race_columns = ['RACEDATE', 'COURSE','GOINGSTRING','DISTANCE','RACECLASS', 'RACETYPE', 'RACEVALUE']
horse_columns = ['HANDICAP', 'WEIGHT','DRAW', 'ODDS', 'finpos']
jockey_columns = ['runcount', 'wincount']
trainer_columns = ['winners']


def create_head_to_head(race, runners, jockeys, trainers):
    race['RACEDATE'] = race['RACEDATE'].apply(lambda x: int(time.mktime(x.timetuple())))
    joined = runners.merge(race, on='RACENUMBER').merge(jockeys,
                                                        left_on='JOCKEY',
                                                        right_on='NAME').merge(trainers,
                                                                               left_on='TRAINER',
                                                                               right_on='NAME')
    horse_data = []
    winners = []
    races = 0
    all_columns = race_columns + horse_columns + jockey_columns + trainer_columns
    dataset = joined[all_columns + ['RACENUMBER']].dropna()
    for r, full_race_df in dataset.groupby('RACENUMBER'):
        race_df = full_race_df.drop_duplicates()
        race_parts = race_df[race_columns].iloc[0].values
        for horse1, horse2 in itertools.combinations(race_df[jockey_columns + trainer_columns + horse_columns].values,2):
            winner = int(horse1[-1] < horse2[-1])
            horse_data.append(np.append(race_parts, (horse1[:-1], horse2[:-1])))
            winners.append(winner)
        races += 1
        if races % 1000 == 0:
            print("{} - {}".format(races,len(winners)))

    h2h_df = pd.DataFrame.from_records(horse_data, columns=[race_columns +
                                                            ['{}_1'.format(x) for x in jockey_columns + trainer_columns + horse_columns[:-1]] +
                                                            ['{}_2'.format(x) for x in jockey_columns + trainer_columns + horse_columns[:-1]]])
    h2h_df['DISTANCE'] = h2h_df['DISTANCE'].applymap(distance_to_yards)
    h2h_df['WEIGHT_1'] = h2h_df['WEIGHT_1'].applymap(stones_to_lbs)
    h2h_df['WEIGHT_2'] = h2h_df['WEIGHT_2'].applymap(stones_to_lbs)
    h2h_df['ODDS_1'] = h2h_df['ODDS_1'].applymap(fraction_to_decimal)
    h2h_df['ODDS_2'] = h2h_df['ODDS_2'].applymap(fraction_to_decimal)
    return h2h_df, pd.Series(winners)

# def get_head_to_head(race,  runners, jockeys, trainers, epoch=training_epoch):
#     race['RACEDATE'] = race['RACEDATE'].apply(lambda x: int(time.mktime(x.timetuple())))
#     joined = runners.merge(race, on='RACENUMBER').merge(jockeys,
#                                                         left_on='JOCKEY',
#                                                         right_on='NAME').merge(trainers,
#                                                                                left_on='TRAINER',
#                                                                                right_on='NAME')
#     horse_data = []
#     winners = []
#     races = 0
#     all_columns = race_columns + horse_columns + jockey_columns + trainer_columns
#     dataset = joined[all_columns + ['RACENUMBER']].dropna()
#     for r, full_race_df in dataset.groupby('RACENUMBER'):
#         race_df = full_race_df.drop_duplicates()
#         race_parts = race_df[race_columns].iloc[0].values
#         for horse1, horse2 in itertools.combinations(race_df[jockey_columns + trainer_columns + horse_columns].values,2):
#             winner = int(horse1[-1] < horse2[-1])
#             horse_data.append(np.append(race_parts, (horse1[:-1], horse2[:-1])))
#             winners.append(winner)
#         races += 1
#         if races % 1000 == 0:
#             print("{} - {}".format(races,len(winners)))
#
#     h2h_df = pd.DataFrame.from_records(horse_data, columns=[race_columns +
#                                                             ['{}_1'.format(x) for x in jockey_columns + trainer_columns + horse_columns[:-1]] +
#                                                             ['{}_2'.format(x) for x in jockey_columns + trainer_columns + horse_columns[:-1]]])
#     h2h_df['DISTANCE'] = h2h_df['DISTANCE'].applymap(distance_to_yards)
#     h2h_df['WEIGHT_1'] = h2h_df['WEIGHT_1'].applymap(stones_to_lbs)
#     h2h_df['WEIGHT_2'] = h2h_df['WEIGHT_2'].applymap(stones_to_lbs)
#     h2h_df['ODDS_1'] = h2h_df['ODDS_1'].applymap(fraction_to_decimal)
#     h2h_df['ODDS_2'] = h2h_df['ODDS_2'].applymap(fraction_to_decimal)

if __name__ == '__main__':
    store = pd.HDFStore(r'c:\Users\Claudio\Dropbox\Tennis Project\HorseRacing\srs.h5')
    h2h, winners = create_head_to_head(store['hrace'], store['hrhorse'], store['jockey'], store['trainer'])
    store['h2h-hr'] = h2h
    store['h2hwinners-hr'] = winners