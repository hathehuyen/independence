def average(numbers):
    """
    Calculate average
    :param numbers: list of numbers
    :return: average
    """
    return float(sum(numbers)) / max(len(numbers), 1)


def sma(data, window):
    """
    Calculates Simple Moving Average
    :param data: list of prices
    :param window: price look back length
    :return: SMA
    """
    if len(data) < window:
        return None
    return sum(data[-window:]) / float(window)


def ema(data, window):
    """
    Calculates Exponential Moving Average
    :param data: list of prices
    :param window: price look back length
    :return: EMA
    """
    if len(data) < 2 * window:
        raise ValueError("data is too short")
    c = 2.0 / (window + 1)
    current_ema = sma(data[-window * 2:-window], window)
    for value in data[-window:]:
        current_ema = (c * value) + ((1 - c) * current_ema)
    return current_ema
