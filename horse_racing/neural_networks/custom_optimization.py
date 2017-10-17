import logging

from keras.layers import K
from keras.losses import binary_crossentropy

_EPSILON = 1e-7
log = logging.getLogger(__name__)


# custom loss functions
class CustomPayoffs():
    def __init__(self, method='back'):
        self.method = method
        log.info("Initialize custom payoff with {}".format(self.method))

    def custom_cross_entropy(self, y_true, y_pred):
        # y_true has the payoffs in the last dimension
        y_true, payoffs = splitter(y_true)

        if self.method == 'lay':
            tp_weight = K.abs(payoffs)
            fp_weight = K.abs(payoffs)
            tn_weight = 1
            fn_weight = 0.95

        elif self.method == 'back':
            tp_weight = K.abs(payoffs)  # opportunity cost
            tn_weight = 0  # opportunity cost
            fp_weight = 1  # cost
            fn_weight = K.abs(payoffs)  # cost

        loss = -K.mean(fn_weight * y_true * K.log(y_pred + _EPSILON) +  # fn cost (not backing if it should)
                       fp_weight * (1 - y_true) * K.log(1 - y_pred + _EPSILON)  # fp cost (backing the wrong one)

                       # + tp_weight * y_true * K.log(1 - y_pred + _EPSILON)  # tp (correctly backing)
                       # + tn_weight * (1 - y_true) * K.log(y_pred + _EPSILON)  # tn (correctly not backing)
                       )

        return loss

    def custom_loss(self):
        return

    def custom_cross_entropy_with_weight_tensor(self, y_true, y_pred):
        # y_true has the payoffs in the last dimension
        y_true, payoffs = splitter(y_true)

        y_pred_pos = K.round(K.clip(y_pred, 0, 1))
        y_pred_neg = 1 - y_pred_pos
        y_pos = K.round(K.clip(y_true, 0, 1))
        y_neg = 1 - y_pos

        # get confusion matrix of all samples in batch as matrix
        tp = (y_pos * y_pred_pos)
        tn = (y_neg * y_pred_neg)
        fn = (y_pos * y_pred_neg)
        fp = (y_neg * y_pred_pos)

        if self.method == 'lay':
            tp_weight = K.abs(payoffs)
            fp_weight = K.abs(payoffs)
            tn_weight = 1
            fn_weight = 0.95

        elif self.method == 'back':
            tp_weight = K.abs(payoffs)  # tp (correctly backing)
            fp_weight = 1  # fp cost (backing the wrong one)
            tn_weight = 0  # tn (correctly not backing)
            fn_weight = K.abs(payoffs)  # fn cost (not backing if it should)

        # Get weights
        weight_tensor = tp_weight * tp + fp_weight * fp + tn_weight * tn + fn_weight * fn

        loss = binary_crossentropy(y_true, y_pred)
        weighted_loss = loss * weight_tensor

        return weighted_loss

    @staticmethod
    def binary_crossentropy_after_split(y_true, y_pred):
        y_true, payoffs = splitter(y_true)
        return K.binary_crossentropy(y_true, y_pred)

    # custom metric functions
    @staticmethod
    def acc(y_true, y_pred):
        y_true, payoffs = splitter(y_true)
        return K.mean(K.equal(y_true, K.round(y_pred)), axis=-1)

    @staticmethod
    def profit(y_true, y_pred):
        y_true, payoffs = splitter(y_true)
        profit = K.round(y_pred) * payoffs
        return K.mean(profit, axis=-1)

    # confusion matrix elements
    @staticmethod
    def tp(y_true, y_pred):
        tp, tn, fn, fp = confusion(y_true, y_pred)
        return tp

    @staticmethod
    def tn(y_true, y_pred):
        tp, tn, fn, fp = confusion(y_true, y_pred)
        return tn

    @staticmethod
    def fn(y_true, y_pred):
        tp, tn, fn, fp = confusion(y_true, y_pred)
        return fn

    @staticmethod
    def fp(y_true, y_pred):
        tp, tn, fn, fp = confusion(y_true, y_pred)
        return fp


def confusion(y_true, y_pred):
    y_true, payoffs = splitter(y_true)
    y_pred_pos = K.round(K.clip(y_pred, 0, 1))
    y_pred_neg = 1 - y_pred_pos
    y_pos = K.round(K.clip(y_true, 0, 1))
    y_neg = 1 - y_pos
    tp = K.sum(y_pos * y_pred_pos) / (_EPSILON + K.sum(y_pos))
    tn = K.sum(y_neg * y_pred_neg) / (_EPSILON + K.sum(y_neg))
    fn = K.sum(y_pos * y_pred_neg) / (_EPSILON + K.sum(y_neg))
    fp = K.sum(y_neg * y_pred_pos) / (_EPSILON + K.sum(y_pos))
    return tp, tn, fn, fp


def splitter(y_true):
    payoffs = y_true[:, 1]
    payoffs = K.expand_dims(payoffs, 1)
    y_true = y_true[:, 0]
    y_true = K.expand_dims(y_true, 1)
    return y_true, payoffs
