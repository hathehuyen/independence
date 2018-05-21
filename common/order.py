from common.ohlcv import OHLCV


class Order(object):
    def __init__(self, time: int, valid_time: int, price: float, side: str):
        """
        Order object
        :param time: order time
        :param valid_time: order life time
        :param price: price
        :param side: buy/sell
        """
        self.status = 'ACTIVE'
        self.side = side
        self.price = price
        self.time = time
        self.valid_time = valid_time
        # print('Open order', self.side, '@', self.price)

    def check_status(self, ohlcv: OHLCV):
        """
        Check status of an order
        :param ohlcv: ohlcv candle object
        :return: order status
        """
        if self.status == 'ACTIVE' and ohlcv.end - self.time >= self.valid_time:
            self.status = 'CANCELED'
            print('Order canceled')
        elif (self.side == 'buy' and ohlcv.low < self.price) or (self.side == 'sell' and ohlcv.high > self.price):
            self.status = 'FILLED'
            # print('Order filled')
        return self.status
