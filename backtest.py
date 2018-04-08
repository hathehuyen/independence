#!/usr/bin/env python
import logging
from datetime import datetime
import time
from db import *

# Log config
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# Candle length milisecond
candle_period = 60000
# Margin available
margin = 1000

# Back test settings
selector = 'bitfinex.BTC-USD'
start = time.mktime(datetime.strptime('201803280000', "%Y%m%d%H%M%S").timetuple()) * 1000
end = time.mktime(datetime.strptime('201804032359', "%Y%m%d%H%M%S").timetuple()) * 1000
# print(start, end)


class OHCLV(object):
    def __init__(self):
        self.start = 0
        self.end = 0
        self.open = 0
        self.high = 0
        self.low = 0
        self.close = 0
        self.volume = 0
        self.buy_volume = 0
        self.sell_volume = 0

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
            self.buy_volume += size
        if side == 'sell':
            self.sell_volume += size
        self.volume += size


class Independence(object):
    def __init__(self, length):
        self.lookback = []
        self.signal = ''
        self.length = length
        self.support = 0
        self.resistance = 0

    def calc(self):
        # Calculate signal
        self.support = 0
        self.resistance = 0
        if len(self.lookback) >= self.length:
            for candle in self.lookback:
                if self.resistance == 0 or candle.close > self.resistance:
                    self.resistance = candle.close
                if self.support == 0 or candle.close < self.support:
                    self.support = candle.close

    def add_candle(self, candle: OHCLV):
        # Add OHCLV candle to list
        if self.support != 0 and self.resistance != 0:
            if candle.close > self.resistance:
                self.signal = 'buy'
            else:
                self.signal = 'none'
            if candle.close < self.support:
                self.signal = 'sell'
            else:
                self.signal = 'none'
        self.lookback.append(candle)
        # Trim list if exceed length
        if len(self.lookback) > self.length:
            self.lookback = self.lookback[len(self.lookback)-self.length:]
        # Calc
        self.calc()


class Position(object):
    def __init__(self, symbol: str='btcusd', base: float=0, amount: float=0):
        self.id = ''
        self.symbol = symbol
        self.status = 'INACTIVE'
        self.base = base
        self.amount = amount
        self.timestamp = 0
        self.swap = 0
        self.pl = 0
        self.pl_pct = 0

    def calc(self, trade):
        if self.base != 0 and self.amount != 0:
            self.pl = trade['price'] * self.amount - self.base * self.amount
            self.pl_pct = self.pl / self.base * self.amount * 100

    def open(self, symbol='btcusd', base: float=0, amount: float=0):
        self.symbol = symbol
        self.status = 'ACTIVE'
        self.base = base
        self.amount = amount

    def close(self):
        self.calc()
        self.status = 'CLOSED'


# Get trades data from db
trade_cursor = trades.find({"selector": selector, "time": {"$lte": end, "$gte": start}}).sort([("time", 1)])
# Back testing
candle = OHCLV()
strategy = Independence(60)
pos = Position()
positions = []
last_signal = ''
for trade in trade_cursor:
    # Add trade to OHLCV candle
    candle.add_trade(trade['time'], trade['size'], trade['price'], trade['size'])
    # print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
    # Complete one OHCLV candle
    if candle.start != 0 and candle.end != 0 and candle.end - candle.start >= candle_period:
        # Add candle to strategy
        strategy.add_candle(candle)
        # print(strategy.signal)
        # We got a new signal that difference from last signal
        if strategy.signal != last_signal:
            logging.info(last_signal + '->' + strategy.signal + ':' + pos.status)
            # print(last_signal, '->', strategy.signal)
            # Open long position
            if strategy.signal == 'buy' and pos.status != 'ACTIVE':
                logging.info('Open long position')
                pos.open('btcusd', int(trade['price']), margin / int(trade['price']))
            # Open short position
            if strategy.signal == 'sell' and pos.status != 'ACTIVE':
                logging.info('Open short position')
                pos.open('btcusd', int(trade['price']), -margin / int(trade['price']))
            last_signal = strategy.signal
        # Calculate position P/L
        if pos.status == 'ACTIVE':
            pos.calc(trade)
            if pos.pl_pct >= 1 or (strategy.signal == 'sell' and pos.amount > 0)\
                    or (strategy.signal == 'buy' and pos.amount < 0):
                pos.close()
                positions.append(pos)
                pos = Position()
        # print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
        candle = OHCLV()

print(pos.pl_pct)
for position in positions:
    print(position.pl)
# for candle in candle_list:
#     print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
