from common.ohlcv import OHLCV


class VolumeBased(object):
    def __init__(self, min_len: int=1, max_len: int=1000, diff: float=1):
        self.lookback = []
        self.signal = ''
        self.diff = diff / 100
        self.min_len = min_len
        self.max_len = max_len
        self.length = min_len
        self.buy_vol = 0
        self.sell_vol = 0

    def calc(self):
        # Calculate buy and sell volume
        self.buy_vol = 0
        self.sell_vol = 0
        if len(self.lookback) >= self.length:
            for i, candle in enumerate(self.lookback):
                if i > self.length:
                    break
                self.buy_vol += candle.buy_vol
                self.sell_vol += candle.sell_vol
        # Adjusting look back period length
        if self.buy_vol != 0:
            if abs((self.buy_vol - self.sell_vol) / self.sell_vol) < self.diff:
                self.length -= 1
            if abs((self.buy_vol - self.sell_vol) / self.sell_vol) > self.diff:
                self.length += 1
            if self.length < self.min_len:
                self.length = self.min_len
            if self.length > self.max_len:
                self.length = self.max_len

    def add_candle(self, candle: OHLCV):
        # Add OHCLV candle to list
        self.lookback.append(candle)
        # Trim list if exceed length
        if len(self.lookback) > self.length:
            self.lookback = self.lookback[len(self.lookback) - self.length:]
        # Calc
        self.calc()
        # Calculate signal

        if self.buy_vol > self.sell_vol * self.diff + self.sell_vol:
            self.signal = 'sell'
        elif self.sell_vol > self.buy_vol * self.diff + self.buy_vol:
            self.signal = 'buy'
        else:
            self.signal = 'none'

