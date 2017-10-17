import keras.backend as K
import pandas as pd
import tensorflow as tf
from keras.optimizers import Adam

from horse_racing.neural_networks.neural_network_mre import FlatNet


def payoff(payoffs):
    def loss(y_true, y_pred):
        # https://stats.stackexchange.com/questions/272754/how-do-interpret-an-cross-entropy-score
        # payoffs [kack, lay, 0, maximum_possible]
        # y_true: [1,0,0] or [0,1,0]

        y_pred

        back_true = y_true[:, :, 0]
        back_pred = y_pred[:, :, 0]
        lay_true = y_true[:, :, 1]
        lay_pred = y_pred[:, :, 1]
        back_loss = K.switch(K.all(K.equal(back_true, back_pred), K.equal(back_pred, 1)), payoffs - 1,
                             K.switch(K.all(K.not_equal(back_true, back_pred), K.equal(back_pred, 1)), -1,
                                      0))

        lay_loss = K.switch(K.all(K.equal(lay_true, lay_pred), K.equal(lay_pred, 1)), 1,
                            K.switch(K.all(K.not_equal(lay_true, lay_pred), K.equal(lay_pred, 1)), -payoffs + 1,
                                     0))

        total_loss = K.mean(lay_loss + back_loss)
        # -(customized_rate * y_true * tensor.log(y_pred) + (1.0 - y_true) * tensor.log(1.0 - y_pred))

        loss = K.mean(K.binary_crossentropy(total_loss), axis=-1)
        return loss

    return loss


def payoff_metrics_true(odds):
    def mean_pred(y_true, y_pred):
        return K.mean(y_pred)

    return mean_pred


def payoff_metrics_actual(odds):
    def mean_actual(y_true, y_pred):
        return K.mean(y_true)

    return mean_actual


class ProfitNet(FlatNet):
    def __init__(self):
        super().__init__()

    def load_sample_data(self):
        self.df = pd.read_csv('sample_data3.csv')

    def get_odds(self):
        self.odds = 1
        self.odds = tf.Variable(tf.ones([len(self.trainX - 1)]))

    def train_model(self):
        self.model.compile(loss=payoff(self.odds),
                           optimizer=Adam(),
                           metrics=[payoff_metrics_actual(self.odds), payoff_metrics_actual(self.odds), 'accuracy'])

        self.model.fit(self.trainX,
                       self.trainY,
                       validation_data=(self.testX, self.testY),
                       epochs=50,
                       batch_size=5000,
                       verbose=1,
                       callbacks=[self.tbCallBack, self.early_stop])

        scores = self.model.evaluate(self.testX, self.testY)
        print("\n%s: %.2f%%" % (self.model.metrics_names[1], scores[1] * 100))

        self.save_model()


def maximize_profit():
    horses = 2
    n = ProfitNet()
    n.load_sample_data()
    n.split_data(horses=horses)
    n.get_odds()
    n.create_model(outputs=horses)
    n.train_model()


if __name__ == '__main__':
    maximize_profit()
