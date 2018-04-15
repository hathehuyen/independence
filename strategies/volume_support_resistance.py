from common.ohlcv import OHLCV


class VolumeSupportResistance(object):
    def __init__(self, min_len: int=1, max_len: int=1000, diff: float=1):
        """
        Volume, support, resistance strategy
        :param min_len: minimum length
        :param max_len: maximum length
        :param diff: difference percentage
        """
        self.lookback = []
        self.signal = ''
        self.min_len = min_len
        self.max_len = max_len
        self.diff = diff / 100
        self.length = min_len
        self.support = 0
        self.resistance = 0
        self.sell_vol = 0
        self.buy_vol = 0

    def calc(self):
        """
        Calculate
        :return: none
        """
        self.support = 0
        self.resistance = 0
        self.sell_vol = 0
        self.buy_vol = 0
        if len(self.lookback) >= self.length:
            for i, candle in enumerate(self.lookback):
                if i > self.length:
                    break
                if self.resistance == 0 or candle.close > self.resistance:
                    self.resistance = candle.close
                if self.support == 0 or candle.close < self.support:
                    self.support = candle.close
                self.buy_vol += candle.buy_vol
                self.sell_vol += candle.sell_vol
        # Adjusting look back period length
        if self.support != 0:
            if (self.resistance - self.support) / self.support < self.diff:
                self.length += 1
            if (self.resistance - self.support) / self.support > self.diff:
                self.length -= 1
            if self.length < self.min_len:
                self.length = self.min_len
            if self.length > self.max_len:
                self.length = self.max_len
        # print(self.length)

    def add_candle(self, candle: OHLCV):
        """
        Add cancle
        :param candle: OHLCV candle
        :return: none
        """
        # Calculate signal
        if self.support != 0 and self.resistance != 0:
            if candle.close >= self.resistance and self.buy_vol / self.sell_vol > self.diff:
                self.signal = 'buy'
                # self.lookback.clear()
            elif candle.close <= self.support and self.sell_vol - self.buy_vol > self.diff:
                self.signal = 'sell'
                # self.lookback.clear()
            else:
                self.signal = 'none'
        # Add OHCLV candle to list
        self.lookback.append(candle)
        # Calc
        self.calc()
        # Trim list if exceed length
        if len(self.lookback) > self.max_len:
            self.lookback = self.lookback[len(self.lookback) - self.max_len:]
