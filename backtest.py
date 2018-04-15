#!/usr/bin/env python
import logging
from datetime import datetime
import time
from db import *
from common.ohlcv import OHLCV
from common.position import Position
from strategies.volume_support_resistance import VolumeSupportResistance

# Log config
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# Margin available
margin = 1000
# Trailing stop percent
trailing_profit_pct = 81
trailing_stop_pct = 1
# Stop loss percent
stop_pct = 81
# Candle length milisecond
# 5 seconds
# candle_period = 5000
candle_period = 60000 * 30
min_length = 1
max_length = 24 * 7
diff = 0.1
# Strategy look back length
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
# Back test data settings
selector = 'bitfinex.BTC-USD'
start = time.mktime(datetime.strptime('201803010000', "%Y%m%d%H%M%S").timetuple()) * 1000
end = time.mktime(datetime.strptime('201803302359', "%Y%m%d%H%M%S").timetuple()) * 1000


# print(start, end)


# Get trades data from db
trade_cursor = trades.find({"selector": selector, "time": {"$lte": end, "$gte": start}}).sort([("time", 1)])
# Back testing
candle = OHLCV()
strategy = VolumeSupportResistance(min_len=min_length, max_len=max_length, diff=diff)
# strategy = Independence(min_len=min_length, max_len=max_length, diff=diff)
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
                logging.info('Open long position @ ' + str(trade['price']) + " length: " + str(strategy.length))
                pos.open('btcusd', int(trade['price']), margin / int(trade['price']))
            # Open short position
            if strategy.signal == 'sell' and pos.status != 'ACTIVE':
                logging.info('Open short position @ ' + str(trade['price']) + " length: " + str(strategy.length))
                pos.open('btcusd', int(trade['price']), -margin / int(trade['price']))
            last_signal = strategy.signal
        # Calculate position P/L
        if pos.status == 'ACTIVE':
            pos.calc(trade)
            if not pos.trailing and (pos.pl_pct <= -stop_pct
                                     or (strategy.signal == 'sell' and pos.amount > 0)
                                     or (strategy.signal == 'buy' and pos.amount < 0)):
                logging.info('Close position by stop-loss @ ' + str(trade['price']) + ' @ ' +
                             str(pos.pl_pct) if pos.pl_pct <= -stop_pct
                             else 'Close position by signal @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
                pos.close()
            if pos.pl_pct >= trailing_profit_pct and not pos.trailing:
                pos.trailing_stop(trailing_stop_pct)
            if pos.status != "CLOSED" and pos.trailing:
                pos.trailing_stop(trailing_stop_pct)
            if pos.status == "CLOSED":
                if pos.trailing:
                    logging.info('Close position by trailing @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
                pl += pos.pl
                logging.info('PL: ' + str(pl))
                positions.append(pos)
                pos = Position()
        # print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
        candle = OHLCV()

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
