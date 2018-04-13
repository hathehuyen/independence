

class OHCLV(object):
    def __init__(self):
        self.start = 0
        self.end = 0
        self.open = 0
        self.high = 0
        self.low = 0
        self.close = 0
        self.volume = 0
        self.buy_vol = 0
        self.sell_vol = 0

    def add_trade(self, trade_time, size, price, side):
        if self.start == 0:
            self.start = trade_time
            self.open = price
        if self.end == 0 or self.end < trade_time:
            self.end = trade_time
            self.close = price
        if self.high == 0 or self.high < price:
            self.high = price
        if self.low == 0 or self.low > price:
            self.low = price
        if side == 'buy':
            self.buy_vol += size
        if side == 'sell':
            self.sell_vol += size
        self.volume += size


class Independence(object):
    def __init__(self, length: int = 60):
        self.lookback = []
        self.signal = ''
        self.length = length
        self.support = 0
        self.resistance = 0

    def calc(self):
        # Calculate support and resistance
        self.support = 0
        self.resistance = 0
        if len(self.lookback) >= self.length:
            for candle in self.lookback:
                if self.resistance == 0 or candle.close > self.resistance:
                    self.resistance = candle.close
                if self.support == 0 or candle.close < self.support:
                    self.support = candle.close

    def add_candle(self, candle: OHCLV):
        # Calculate signal
        if self.support != 0 and self.resistance != 0:
            if candle.close >= self.resistance:
                self.signal = 'sell'
            elif candle.close <= self.support:
                self.signal = 'buy'
            else:
                self.signal = 'none'
        # Add OHCLV candle to list
        self.lookback.append(candle)
        # Trim list if exceed length
        if len(self.lookback) > self.length:
            self.lookback = self.lookback[len(self.lookback) - self.length:]
        # Calc
        self.calc()
