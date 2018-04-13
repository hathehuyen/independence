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
# 5 seconds
candle_period = 5000
# Strategy look back length
strategy_length = 1550
# # 1 hours
# strategy_length = 720
# # 2 hours
# strategy_length = 1440
# good at 2017-08
# strategy_length = 1600
# strategy_length = 1700
# # 3 hours
# strategy_length = 2160
# 4 hours
# strategy_length = 2880
# # 5 hours
# strategy_length = 3600
# # 6 hours
# strategy_length = 4320
# Margin available
margin = 1000
# Trailing stop percent
trailing_profit_pct = 4
trailing_stop_pct = 1
# Stop loss percent
stop_pct = 3
# Back test data settings
selector = 'bitfinex.BTC-USD'
start = time.mktime(datetime.strptime('201708010000', "%Y%m%d%H%M%S").timetuple()) * 1000
end = time.mktime(datetime.strptime('201803302359', "%Y%m%d%H%M%S").timetuple()) * 1000


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
                self.signal = 'buy'
            elif candle.close <= self.support:
                self.signal = 'sell'
            else:
                self.signal = 'none'
        # Add OHCLV candle to list
        self.lookback.append(candle)
        # Trim list if exceed length
        if len(self.lookback) > self.length:
            self.lookback = self.lookback[len(self.lookback) - self.length:]
        # Calc
        self.calc()


class VolumeBased(object):
    def __init__(self, length: int = 60):
        self.lookback = []
        self.signal = ''
        self.length = length
        self.buy_vol = 0
        self.sell_vol = 0

    def calc(self):
        # Calculate support and resistance
        self.buy_vol = 0
        self.sell_vol = 0
        if len(self.lookback) >= self.length:
            for candle in self.lookback:
                self.buy_vol += candle.buy_vol
                self.sell_vol += candle.sell_vol
        # Calculate signal
        # print("Vol", self.buy_vol, self.sell_vol)
        if self.buy_vol > self.sell_vol * 1.2:
            self.signal = 'sell'
        elif self.sell_vol > self.buy_vol * 1.2:
            self.signal = 'buy'
        else:
            self.signal = 'none'

    def add_candle(self, candle: OHCLV):
        # Add OHCLV candle to list
        self.lookback.append(candle)
        # Calculate signal
        self.calc()
        # Trim list if exceed length
        if len(self.lookback) > self.length:
            self.lookback = self.lookback[len(self.lookback) - self.length:]


class Position(object):
    def __init__(self, symbol: str = 'btcusd', base: float = 0, amount: float = 0):
        self.id = ''
        self.symbol = symbol
        self.status = 'INACTIVE'
        self.base = base
        self.amount = amount
        self.timestamp = 0
        self.swap = 0
        self.pl = 0
        self.pl_pct = 0
        self.trailing = False
        self.last_pl_pct = 0

    def calc(self, trade):
        if self.base != 0 and self.amount != 0:
            self.pl = trade['price'] * self.amount - self.base * self.amount
            self.pl_pct = self.pl / abs(self.base * self.amount) * 100

    def open(self, symbol='btcusd', base: float = 0, amount: float = 0):
        self.symbol = symbol
        self.status = 'ACTIVE'
        self.base = base
        self.amount = amount

    def close(self):
        self.status = 'CLOSED'

    def trailing_stop(self, trade, percent: float = 0):
        self.trailing = True
        if self.last_pl_pct == 0:
            self.last_pl_pct = self.pl_pct
        elif self.pl_pct > self.last_pl_pct:
            self.last_pl_pct = self.pl_pct
        elif self.last_pl_pct - self.pl_pct >= percent:
            self.close()


# Get trades data from db
trade_cursor = trades.find({"selector": selector, "time": {"$lte": end, "$gte": start}}).sort([("time", 1)])
# Back testing
candle = OHCLV()
strategy = VolumeBased(strategy_length)
# strategy = Independence(strategy_length)
pos = Position()
positions = []
last_signal = ''
pl = 0
for trade in trade_cursor:
    # Add trade to OHLCV candle
    candle.add_trade(trade['time'], trade['size'], trade['price'], trade['side'])
    # print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
    # Complete one OHCLV candle
    if candle.start != 0 and candle.end != 0 and candle.end - candle.start >= candle_period:
        # Add candle to strategy
        # print(candle.volume, candle.sell_vol, candle.buy_vol)
        strategy.add_candle(candle)
        # print(strategy.signal)
        # We got a new signal that difference from last signal
        if strategy.signal != last_signal:
            # logging.info(last_signal + '->' + strategy.signal + ':' + str(trade['price']))
            # print(last_signal, '->', strategy.signal)
            # Open long position
            if strategy.signal == 'buy' and pos.status != 'ACTIVE':
                logging.info('Open long position @ ' + str(trade['price']))
                pos.open('btcusd', int(trade['price']), margin / int(trade['price']))
            # Open short position
            if strategy.signal == 'sell' and pos.status != 'ACTIVE':
                logging.info('Open short position @ ' + str(trade['price']))
                pos.open('btcusd', int(trade['price']), -margin / int(trade['price']))
            last_signal = strategy.signal
        # Calculate position P/L
        if pos.status == 'ACTIVE':
            pos.calc(trade)
            if not pos.trailing and (pos.pl_pct <= -stop_pct
                                     or (strategy.signal == 'sell' and pos.amount > 0)
                                     or (strategy.signal == 'buy' and pos.amount < 0)):
                logging.info('Close position by stop-loss @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct) if pos.pl_pct <= -stop_pct
                             else 'Close position by signal @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
                pos.close()
            if pos.pl_pct >= trailing_profit_pct and not pos.trailing:
                pos.trailing_stop(trade, trailing_stop_pct)
            if pos.status != "CLOSED" and pos.trailing:
                pos.trailing_stop(trade, trailing_stop_pct)
            if pos.status == "CLOSED":
                if pos.trailing:
                    logging.info('Close position by trailing @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
                pl += pos.pl
                logging.info('PL: ' + str(pl))
                positions.append(pos)
                pos = Position()
        # print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
        candle = OHCLV()

# print(pos.base, pos.amount, pos.pl, pos.pl_pct)
profit = 0
wins = 0
loses = 0
for position in positions:
    # print(position.pl)
    profit += position.pl
    if position.pl > 0:
        wins += 1
    else:
        loses += 1
print(len(positions), 'position traded over', (end - start) / 1000 / 60 / 60 / 24, 'days')
print('Wins/Loses:', wins, '/', loses)
fee = len(positions) * margin * 0.004
print('Profit:', profit, profit - fee)
print('Max trading fee (taker):', fee)
# for candle in candle_list:
#     print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
