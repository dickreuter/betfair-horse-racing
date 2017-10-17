from horse_racing.reinforced_learning.qlearning4k.games.snake import Snake
from keras.layers import *
from keras.models import Sequential
from keras.optimizers import *

from horse_racing.reinforced_learning.qlearning4k.agent import Agent

K.set_image_dim_ordering('th')

grid_size = 10
nb_frames = 4
nb_actions = 5

model = Sequential()
model.add(Conv2D(16, (3, 3), activation='relu', input_shape=(nb_frames, grid_size, grid_size)))
model.add(Conv2D(32, (3, 3), activation='relu'))
model.add(Flatten())
model.add(Dense(256, activation='relu'))
model.add(Dense(nb_actions))
model.compile(RMSprop(), 'MSE')

snake = Snake(grid_size)

agent = Agent(model=model, memory_size=-1, nb_frames=nb_frames)
agent.train(snake, batch_size=64, nb_epoch=10000, gamma=0.8)
agent.play(snake)
