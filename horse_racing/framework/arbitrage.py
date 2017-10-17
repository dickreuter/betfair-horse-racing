from horse_racing.matchbook_manager.engine import Container as MBContainer
from horse_racing.betfair_manager.engine import Container as BFContainer


class GenericRunner(object):

    expoure_limit = 50

    def __init__(self, runner, type):
        self.runner = runner
        self.type = type
        self.best_mb_back = 0
        self.make_bf_bet = 0
        self.mb_runner_id = 0
        self.bf_runner_id = 0

    def make_bf_bet(self, side, amount):
        pass

    def make_mb_bet(self, side, amount):
        pass

    def check_arbitrage(self):
        if self.best_mb_back > self.best_bf_lay:
            self.make_bf_bet('BACK', 2.)
            self.make_mb_bet()
            return
        if self.best_bf_back > self.best_mb_lay:
            self.make_mb_bet('BACK', 2.)
            self.make_bf_bet()
            return

    def profit(self):
        pass

class HorseRace(object):

    def check_arbitrage(self):

        for r in self.runners:
            pass

def _get_bf_market(venue, start, markets):
    for e,mlist in markets.items():
        for m in mlist:
            if venue == m[1].event.venue.lower() and start == '{}.000Z'.format(m[1].market_start_time.isoformat()):
                return m[0]
    return None

def compare(bf, mb):
    mb_markets = mb.get_races()
    events, markets = bf.get_all_races()
    prices = bf.update_markets(events, markets)
    for m in mb_markets:
        bf_market = _get_bf_market(m['venue'],m['marketstart'],markets)
        for p in prices:
            pass

if __name__ == '__main__':
    m = MBContainer()
    bf = BFContainer()
    compare(bf, m)