import numpy as np

from horse_racing.reinforced_learning.qlearning4k.games.game import Game
from horse_racing.utils.tools import get_config


class BettingGame(Game):
    def __init__(self):
        self.won = False
        self.race_number = 0
        self.reset()
        self.profit_per_game = 0

    def reset(self):
        self.race_number = 0

    @property
    def name(self):
        return "Horse Betting"

    @property
    def nb_actions(self):
        return 3

    def play(self, action):
        assert action in range(5), "Invalid action."
        self.scored = 0
        if action == 9:
            pass
            self.ltp = 0
            self.back = False
            self.lay = False

    def get_state(self):
        LTP = 0
        mean = 0
        median = 0
        min_ltp = 0
        max_ltp = 0

        values = np.array([LTP, mean, median, min_ltp, max_ltp])
        self.race_number += 1
        return values

    def get_score(self):
        config = get_config()
        self.back_pnl = [0]
        self.lay_pnl = [0]
        fees = config.getfloat("Betting", "fees")
        stake = config.getfloat("Betting", "Stake")
        won = np.nan
        loser = np.nan
        LTP = self.ltp

        if won and self.back:  # back on winner
            change = (LTP * stake - stake) * (1 - fees)
            self.back_pnl.append(change)
        if won and self.lay:  # lay on winner
            change = -(LTP * stake - stake)
            self.lay_pnl.append(change)
        if loser and self.back:  # back on loser
            change = -stake  # pylint: disable=E1130
            self.back_pnl.append(change)
        if loser and self.lay:  # lay on loser
            change = stake * (1 - fees)
            self.lay_pnl.append(change)

        total_profit = sum(self.lay_pnl) + sum(self.back_pnl)
        return total_profit

    def is_over(self):
        if self.race_number > 1000:
            return True
        else:
            return False

    def is_won(self):
        return self.profit_per_game > 0.4
