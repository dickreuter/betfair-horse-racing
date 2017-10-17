import numpy as np


def predictions_to_probabilities(matrix, as_odds=False):
    """
    Give a matrix of head to head probs, return normalized prob for each runner
    :param matrix: 
    :return: 
    """
    x, y = matrix.shape
    if x != y:
        raise AttributeError("Input matrix needs to be square")
    xp, yp = np.where(matrix > 1.)
    if len(xp) or len(yp):
        raise AttributeError("Matrix contains prob > 1.")
    if not (matrix.diagonal()==np.ones(x)).all():
        raise AttributeError("Diagionals must be unity")
    raw_probs = matrix.cumprod(axis=1)[:,-1]
    weighted_probs = raw_probs / raw_probs.sum()
    if as_odds:
        return 1 / weighted_probs
    return weighted_probs

if __name__ == '__main__':
    test_data = np.array([[1,.2,.3],[.8,1.,.5],[.7,.5,1.]])
    print(predictions_to_probabilities(test_data))