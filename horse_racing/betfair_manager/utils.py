import re

distance_re = re.compile(r'([0-9]{1,})([MmFfyy])')
odds_re = re.compile(r'([0-9]{1,})[-/]{1}([0-9]{1,})')


def fraction_to_decimal(odds):
    """
    Converts fractional e.g. 2-1 to decimal to 2
    :param odds: 
    :return: 
    """
    if isinstance(odds, str) and odds.lower().startswith('evens'):
        return 2.
    try:
        parts = list(map(float, odds_re.findall(odds)[0]))
        return 1 + parts[0] / parts[1]
    except:
        return 2.

def stones_to_lbs(weight):
    """
    Converts St Lbs to lbs
    :param weight: 
    :return: 
    """
    try:
        parts = list(map(float, weight.split('-')))
        return parts[0] * 14 + parts[1]
    except:
        return None

def distance_to_yards(distance):
    """
    Return the length in yards of the race length
    :param distance: 
    :return: 
    """
    race_length = 0
    for length, factor in distance_re.findall(distance):
        if factor == 'f' or factor == 'F':
            scalar = 220
        elif factor == 'M' or factor == 'm':
            scalar = 1760
        else:
            scalar = 1
        race_length += scalar * int(length)
    return race_length