import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

diffs = pd.DataFrame.from_csv('c:/temp/returns.csv').values.flatten()
stake = 1
stakes= []

cumulative_returns = [1000]
for diff in diffs:
    scaled_diff = diff * stake
    current_return = cumulative_returns[-1] + scaled_diff
    cumulative_returns.append(current_return)
    last_balance = cumulative_returns[-1]
    stake = max(np.clip((last_balance-1250)/250,1,10),stake)
    stakes.append(stake)
    # stake =np.clip(last_balance,1,1000) # reduce after


plt.plot(cumulative_returns, 'b', label='total')
print (min(cumulative_returns))
print (max(stakes))
plt.show()

# result: increase balance by 1 for every 250 above 1000 up to 10. Minimum balance from 100 will be 700 and end result is 10k