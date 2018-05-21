from common import tools
from common.ohlcv import OHLCV


class MACD(object):
    def __init__(self, short: int=12, long: int=26):
        self.short = short
        self.long = long
        self.lookback = []
        self.ma_short = 0
        self.ma_long = 0
        self.macd = None

    def add_candle(self, candle: OHLCV):
        """
        Add OHLCV candle
        :param candle: OHLCV candle
        :return: macd
        """
        # Add candle to look back list
        self.lookback.append(candle)
        # Trim list if exceed length
        if len(self.lookback) > self.long:
            self.lookback = self.lookback[len(self.lookback) - self.long:]
        # Calculate
        self.calc()
        return self.macd

    def calc(self):
        """
        Calculate average values
        :return: none
        """
        if len(self.lookback) >= self.long:
            self.ma_long = tools.average([i.close for i in self.lookback])
            self.ma_short = tools.average([i.close for i in self.lookback[self.long - self.short:]])
            self.macd = self.ma_short - self.ma_long

