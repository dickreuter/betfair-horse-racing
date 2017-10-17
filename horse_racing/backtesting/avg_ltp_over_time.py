from datetime import datetime, timedelta

import numpy as np
from matplotlib import pyplot as plt

from horse_racing.utils.mongo_manager import MongoManager


def avg_ltp_for_winner():
    start = -3 * 60
    end = 10 * 60
    step = 10
    x = np.arange(start, end, step)

    buckets = (x).tolist()

    m = MongoManager(use_remote=True, use_archive=False)
    from_date = datetime.now() - timedelta(days=1000)  # datetime(2018, 2, 28)
    to_date = datetime.now()
    ltp = m.get_avg_ltp_by_time_to_start_bucketed('LTP', 'avg', buckets, from_date, to_date,
                                                  countrycode=['UK', 'IE'],
                                                  col='price_scrape_tickdata')
    print(ltp)

    LTPs = [v['avg_ltp'] for v in ltp]

    print("Best time to place lays is {} minutes before race start.".format(np.argmin(LTPs)))
    plt.plot(x, LTPs)
    plt.show()


if __name__ == '__main__':
    avg_ltp_for_winner()
