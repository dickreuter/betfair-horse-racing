import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle


def read_dataset():
    horses = 1
    df = pd.read_csv('c:/temp/2016.csv', index_col=0)
    x = df[['LTP','kurtosis']].values.astype('float32')
    y = df['win'].astype('int')
    y=y.reshape(-1,1)
    payoffs = df['lay'].values
    return x, y, payoffs



def multiplayer_perceptron(x, weights, biases):
    layer_1 = tf.add(tf.matmul(x, weights['h1']), biases['b1'])
    layer_1 = tf.nn.sigmoid(layer_1)

    layer_2 = tf.add(tf.matmul(layer_1, weights['h2']), biases['b2'])
    layer_2 = tf.nn.sigmoid(layer_2)

    layer_3 = tf.add(tf.matmul(layer_2, weights['h3']), biases['b3'])
    layer_3 = tf.nn.sigmoid(layer_3)

    layer_4 = tf.add(tf.matmul(layer_3, weights['h4']), biases['b4'])
    layer_4 = tf.nn.sigmoid(layer_4)

    out_layer = tf.matmul(layer_4, weights['out']) + biases['out']
    return out_layer


if __name__ == '__main__':
    X, Y, payoffs = read_dataset()
    # X, Y = shuffle(X, Y, random_state=1)
    train_x, test_x, train_y, test_y = train_test_split(X, Y, test_size=0.2, random_state=1)

    print(train_x.shape)
    print(train_y.shape)
    print(test_x.shape)
    print(test_y.shape)

    learning_rate = 0.1
    training_epochs = 50
    cost_history = np.empty(shape=[1], dtype=float)

    n_dim = X.shape[1]
    print("n_dim", n_dim)
    n_class = 1
    print("n_class", n_class)

    n_hidden_1 = 20
    n_hidden_2 = 40
    n_hidden_3 = 20
    n_hidden_4 = 10

    x = tf.placeholder(tf.float32, [None, n_dim])
    W = tf.Variable(tf.zeros([n_dim, n_class]))
    b = tf.Variable(tf.zeros([n_class]))
    y_ = tf.placeholder(tf.float32, [None, n_class])

    weights = {
        'h1': tf.Variable(tf.truncated_normal([n_dim, n_hidden_1])),
        'h2': tf.Variable(tf.truncated_normal([n_hidden_1, n_hidden_2])),
        'h3': tf.Variable(tf.truncated_normal([n_hidden_2, n_hidden_3])),
        'h4': tf.Variable(tf.truncated_normal([n_hidden_3, n_hidden_4])),
        'out': tf.Variable(tf.truncated_normal([n_hidden_4, n_class]))
    }

    biases = {
        'b1': tf.Variable(tf.truncated_normal([n_hidden_1])),
        'b2': tf.Variable(tf.truncated_normal([n_hidden_2])),
        'b3': tf.Variable(tf.truncated_normal([n_hidden_3])),
        'b4': tf.Variable(tf.truncated_normal([n_hidden_4])),
        'out': tf.Variable(tf.truncated_normal([n_class]))
    }

    init = tf.global_variables_initializer()
    saver = tf.train.Saver()

    y = multiplayer_perceptron(x, weights, biases)

    cost_function = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=y, labels=y_))
    training_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(cost_function)

    sess = tf.Session()
    sess.run(init)

    mse_history = []
    accuracy_history = []

    for epoch in range(training_epochs):
        sess.run(training_step, feed_dict={x: train_x, y_: train_y})
        cost = sess.run(cost_function, feed_dict={x: train_x, y_: train_y})
        cost_history = np.append(cost_history, cost)
        correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

        pred_y = sess.run(y, feed_dict={x: test_x})
        mse = tf.reduce_mean(tf.square(pred_y - test_y))
        mse_ = sess.run(mse)

        mse_history.append(mse_)
        accuracy = (sess.run(accuracy, feed_dict={x: train_x, y_: train_y}))
        accuracy_history.append(accuracy)

        print('epoch: ', epoch, ' - ', 'cost: ', cost, " - MSE: ", mse_, " - Train accuracy: ", accuracy)

    # save_path = saver.save(sess, "/Graph")
    # print("Model saved in %s" % save_path)

    plt.plot(mse_history, 'r')
    plt.show()
    plt.plot(accuracy_history)
    plt.show()

    correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    print("Test Accuracy: ", (sess.run(accuracy, feed_dict={x: test_x, y_: test_y})))

    pred_y = sess.run(y, feed_dict={x: test_x})
    mse = tf.reduce_mean(tf.square(pred_y - test_y))
    print("MSE %.4f" % sess.run(mse))
