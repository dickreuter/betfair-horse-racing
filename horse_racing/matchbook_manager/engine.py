from matchbook import APIClient
import datetime as dt

from horse_racing.utils.mongo_manager import Singleton
from horse_racing.utils.tools import get_config


class Container(object, metaclass=Singleton):
    def __init__(self):
        self.selected_events = {}
        self.markets = {}
        self.api = None
        self.do_login()

    def do_login(self):
        config = get_config()
        username = config.get("Matchbook", "username")
        password = config.get("Matchbook", "password")
        self.api = APIClient(username, password)
        # try:
        self.api.login()
        sport_ids = self.api.reference_data.get_sports()
        self.horse_racing = list(filter(lambda x: x['name'] == 'Horse Racing', sport_ids))[0]['id']

    def get_races(self):
        horse_races = self.api.market_data.get_events(sport_ids=self.horse_racing,
                                                      before=int(
                                                          (dt.datetime.now() + dt.timedelta(minutes=70)).timestamp()))
        results = {}
        for e in horse_races:
            location = list(filter(lambda x: x['type'] == 'LOCATION', e['meta-tags']))[0]['name']
            market_time = e['start']
            for m in e['markets']:
                if m['name'] != 'WIN':
                    continue
                d = location, market_time
                results[d] = m
        return results

    def update_race(self, event_id, market_id):
        price_data = self.api.market_data.get_markets(event_id, market_id)
        for market in price_data:
            yield market['id'], market['runners']



