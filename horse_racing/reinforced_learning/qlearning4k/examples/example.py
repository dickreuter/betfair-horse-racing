from horse_racing.reinforced_learning.qlearning4k.games.catch import Catch
from keras.layers import Dense, Flatten
from keras.models import Sequential
from keras.optimizers import sgd

from horse_racing.reinforced_learning.qlearning4k.agent import Agent

nb_frames = 1
grid_size = 10
hidden_size = 100

model = Sequential()
model.add(Flatten(input_shape=(nb_frames, grid_size, grid_size)))
model.add(Dense(hidden_size, activation='relu'))
model.add(Dense(hidden_size, activation='relu'))
model.add(Dense(3))
model.compile(sgd(lr=.2), "mse")

game = Catch(grid_size)
agent = Agent(model)
agent.train(game)
agent.play(game)