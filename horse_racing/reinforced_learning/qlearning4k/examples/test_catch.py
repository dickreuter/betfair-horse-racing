from horse_racing.reinforced_learning.qlearning4k.games.catch import Catch
from keras.layers import Flatten, Dense
from keras.models import Sequential
from keras.optimizers import *

from horse_racing.reinforced_learning.qlearning4k.agent import Agent

grid_size = 10
hidden_size = 100
nb_frames = 1

model = Sequential()
model.add(Flatten(input_shape=(nb_frames, grid_size, grid_size)))
model.add(Dense(hidden_size, activation='relu'))
model.add(Dense(hidden_size, activation='relu'))
model.add(Dense(3))
model.compile(sgd(lr=.2), "mse")

catch = Catch(grid_size)
agent = Agent(model=model)
agent.train(catch, batch_size=10, nb_epoch=1000, epsilon=.1)
agent.play(catch)
