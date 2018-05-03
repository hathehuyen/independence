from common.ohlcv import OHLCV


class Order(object):
    def __init__(self, price: float, side: str='buy'):
        self.status = 'ACTIVE'
        self.side = side
        self.price = price

    def check_status(self, ohlcv: OHLCV):
        if (self.side == 'buy' and ohlcv.low < self.price) or (self.side == 'sell' and ohlcv.high > self.price):
            self.status = 'FILLED'
