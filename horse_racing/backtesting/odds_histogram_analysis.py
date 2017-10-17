
import matplotlib.pyplot as plt
import numpy as np

from horse_racing.neural_networks.lay_all import LayAll

n = LayAll()

n.load_enriched_ts(from_year=2015, to_year=2018, localhost=False, strategy='lay', countrycode= ['GB'])
n.load_model()

# create an array with shape [races (this can be a single race), features_per_horse * horses, 1)
X = n.X

b=1/(n.df[n.df['winner']==True]['lay_risk'].abs()+1)
c=1/(n.df[n.df['winner']==False]['lay_risk'].abs()+1)
# fig2=b.hist(bins=100,normed=True)
winner = np.histogram(b, bins=50)
loser = np.histogram(c, bins=50)

ratio=loser[0]/winner[0]
plt.bar(x=np.arange(0,1,.02),height=ratio, width=.01)
plt.plot(np.arange(0,1,.02),1/(np.arange(0,1,.02))-1,'g-')
plt.ylim(ymax=50)
plt.title("loser/winner ratio")
plt.show()

print ("Mean lay risk odds: {}".format(np.mean(n.lay_risk)))
print ("Median lay risk odds: {}".format(np.median(n.lay_risk)))