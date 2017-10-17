from horse_racing.reinforced_learning.betting import BettingGame
from keras.layers import Dense, Flatten
from keras.models import Sequential
from keras.optimizers import sgd

from horse_racing.reinforced_learning.qlearning4k.agent import Agent

horses = 10
nb_frames = 1
hidden_size = 100
grid_size = 12

model = Sequential()
model.add(Flatten(input_shape=(5)))
model.add(Dense(hidden_size, activation='relu'))
model.add(Dense(hidden_size, activation='relu'))
model.add(Dense(2))
model.compile(sgd(lr=.2), "mse")

game = BettingGame()
agent = Agent(model)
agent.train(game)
agent.play(game)
