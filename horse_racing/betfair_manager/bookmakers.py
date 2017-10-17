import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
from collections import OrderedDict
import time

import logging
log = logging.getLogger(__name__)

bookmaker_map = {}
bookmaker_map['chelmsford city'] = 'chelmsford-city'
bookmaker_map['dover downs'] = 'dover-downs'
bookmaker_map['sunland park'] = 'sunland-park'
bookmaker_map['turf paradise'] = 'turf-paradise'

# These courses are not present on oddschecker.
missing_courses = [ 'avondale', 'dover downs']

def _map_bookies(bookie):
    try:
        return bookmaker_map[bookie]
    except:
        return bookie

def _adjust_time(time_s):
    """
    BF market times are in GMT, this adjusts the time if daylight savings applicable.
    :param time_s: 
    :return: 
    """
    h, m = time_s.split(':')
    adjustment = time.localtime().tm_isdst
    if adjustment:
        h = int(h) + adjustment
        if h < 10:
            h = '0{}'.format(h)
        else:
            h = str(h)
    return '{}:{}'.format(h, m)


def get_odds_list(url, decimal=True):
    key = 'data-odig' if decimal else 'data-o'

    r = requests.get(url)
    soup = bs(r.text, 'lxml')

    head = soup.find('tr', {'class': 'eventTableHeader'})
    if not head:
        log.debug("Could not parse {}".format(url))
        return

    headers = [h.aside.a['title'] for h in head.find_all('td') if hasattr(h.aside, 'a')]
    table = soup.find('tbody', {'id': 't1'})
    rows = []
    for row in table.find_all('tr'):
        odds = OrderedDict(zip(headers, [td[key] for td in row.find_all('td') if td.has_attr(key)]))
        odds['Name'] = row['data-bname']
        rows.append(odds)

    try:
        race_status = {}
        race_status_xml = soup.find('ul', {'id': 'race-headline-info'})
        for r in race_status_xml.find_all('li'):
            key = r.find_next('span').text.strip().rstrip(':')
            value = r.find_next('span').find_next('span').text.strip()
            race_status[key] = value
    except:
        race_status = {}

    return rows, race_status

def get_odds(url, decimal=True):
    result_dict, race_status = get_odds_list(url, decimal)
    if pd.DataFrame.from_dict(result_dict).empty:
        return pd.DataFrame(), race_status
    return pd.DataFrame.from_dict(result_dict).set_index('Name'), race_status

def get_race_odds(venue, start, runners):
    url = 'https://www.oddschecker.com/horse-racing/{}/{}/winner'.format(_map_bookies(venue),
                                                                         _adjust_time(start.strftime('%H:%M')))
    df, race_status = get_odds(url)
    if not df.empty:
        runner_names = list(df.index)
        for i, name in enumerate(runner_names):
            for r in runners:
                if r.runner_name.lower() == name.lower():
                    runner_names[i] = r.selection_id
        df.index = runner_names
    return df, race_status

if __name__ == '__main__':
    url = 'https://www.oddschecker.com/horse-racing/windsor/13:40/winner'
    print(get_odds(url))