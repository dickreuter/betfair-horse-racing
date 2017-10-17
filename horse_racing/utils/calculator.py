import enum
#
# class CommissionType(enum):
#
#     NOCOMMISSION = 0
#     WINONLY = 1
#     BOTH = 2

class ArbitrageEngine(object):


    def __init__(self, commissions):
        self.commissions = commissions


    def get_arbitrage(self, prices, sizes):
        """
        A sequence of prices for each exchange of the form (back, lay)
        :param prices: 
        :returns: index of back, index of lay or None, None
        """
        best_back = max([x[0] for x in prices])
        best_lay = min([x[1] for x in prices])
        if best_back < best_lay:
            # No arb :(
            return None

        best_back_exchange = [x[0] for x in prices].index(best_back)
        best_lay_exchange = [x[1] for x in prices].index(best_lay)

        max_stake = min(sizes[best_back_exchange][0], sizes[best_lay_exchange][1])

        # Determine stakes to place on either side to equalize payout

        profit_back = best_back * max_stake * (1-self.commissions[best_back_exchange])
        lay_profit = profit_back / (1-self.commissions[best_lay_exchange])

        lay_size = lay_profit / best_lay

        return (best_back_exchange, sizes[best_back][0]) , (best_lay_exchange, lay_size)

if __name__ == '__main__':
    ae = ArbitrageEngine([0.05,0.02])
    ae.get_arbitrage([(1.2,5), (6, 7)], [(100,100), (75, 85)])
