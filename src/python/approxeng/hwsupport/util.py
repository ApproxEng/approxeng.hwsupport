# -*- coding: future_fstrings -*-

import logging

LOGGER = logging.getLogger(name='approxeng.hwsupport.util')


def check_range(i):
    """
    Accepts a number, returns that number clamped to a range of -1.0 to 1.0, as a float
    :param i:
        Number
    :return:
        Float between -1.0 and 1.0
    """
    f = float(i)
    if f < -1.0:
        LOGGER.warning('check_range: Value < -1.0, returning -1.0')
        return -1.0
    if f > 1.0:
        LOGGER.warning('check_range: Value > 1.0, returning 1.0')
        return 1.0
    return f


def check_positive_range(i):
    """
    Clamp to float range 0..1
    """
    f = float(i)
    if f < 0.0:
        LOGGER.warning('check_positive: Value < 0, returning 0')
        return 0.0
    if f > 1.0:
        LOGGER.warning('check_positive: Value > 1.0, returning 1.0')
        return 1.0
    return f


def check_positive(i):
    """
    Ensure positive, clamp to float range 0..
    """
    f = float(i)
    if f < 0.0:
        LOGGER.warning('check_positive: Value < 0, returning 0')
        return 0.0
    return f
