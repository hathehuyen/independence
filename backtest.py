#!/usr/bin/env python
import logging
import time
from db import *
from common.ohlcv import OHLCV
from common.order import Order
from common.position import Position
# from strategies.volume_support_resistance import VolumeSupportResistance
# from strategies.volume_based import VolumeBased
from strategies.retrace import Retrace
import matplotlib.pyplot as plt
from datetime import datetime

# Log config
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# Margin available
margin = 1000
# Candle length milisecond
# 5 seconds
# candle_period = 5000
candle_period = 60000
min_length = 120
max_length = 120
diff = 4
order_diff = 1
order_valid_time = 60000 * 15
# Back test data settings
selector = 'bitfinex.BTC-USD'
start = time.mktime(datetime.strptime('201702150000', "%Y%m%d%H%M%S").timetuple()) * 1000
end = time.mktime(datetime.strptime('201804152359', "%Y%m%d%H%M%S").timetuple()) * 1000

# Trailing stop percent
trailing_profit_pct = 100
trailing_stop_pct = 0.1
# Stop loss percent
stop_pct = 100

# print(start, end)


# Get trades data from db
trade_cursor = trades.find({"selector": selector, "time": {"$lte": end, "$gte": start}}).sort([("time", 1)])
# Back testing
candle = OHLCV()
strategy = Retrace(min_len=min_length, max_len=max_length, diff=diff)
# strategy = VolumeBased(min_len=min_length, max_len=max_length, diff=diff)
# strategy = VolumeSupportResistance(min_len=min_length, max_len=max_length, diff=diff)
# strategy = Independence(min_len=min_length, max_len=max_length, diff=diff)
order = None
pos = Position()
positions = []
last_signal = None
pl = 0
price_index = []
price_value = []
buy_index = []
buy_value = []
sell_index = []
sell_value = []
pl_index = []
pl_value = []
for trade in trade_cursor:
    # Add trade to OHLCV candle
    candle.add_trade(trade['time'], trade['size'], trade['price'], trade['side'])
    # print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
    # Complete one OHCLV candle
    if candle.start != 0 and candle.end != 0 and candle.end - candle.start >= candle_period:
        price_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        price_value.append(candle.close)
        # Add candle to strategy
        strategy.add_candle(candle)
        # We got a new signal that difference from last signal => open an order
        if strategy.signal and strategy.signal != last_signal:
            if pos.status != 'ACTIVE':
                if not order:
                    if strategy.signal == 'buy':
                        price = candle.close - (candle.close * order_diff / 100)
                    elif strategy.signal == 'sell':
                        price = candle.close + (candle.close * order_diff / 100)
                    else:
                        price = candle.close
                    order = Order(candle.end, order_valid_time, price, strategy.signal)
        # Check order status
        if order:
            if order.status == 'ACTIVE':
                order.check_status(candle)
            if order.status == 'FILLED':
                if order.side == 'buy':
                    logging.info('Open long position @ ' + str(order.price) + " diff: " + str(strategy.up_percent * 100))
                    pos.open('btcusd', order.price, margin / float(order.price))
                    buy_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
                    buy_value.append(order.price)
                if order.side == 'Sell':
                    logging.info('Open short position @ ' + str(order.price) + " diff: " + str(strategy.down_percent * 100))
                    pos.open('btcusd', order.price, -margin / float(order.price))
                    sell_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
                    sell_value.append(order.price)
                stop_pct = strategy.down_percent * 100 / 2
                trailing_profit_pct = stop_pct
                order = None
            elif order.status == 'CANCELED':
                order = None
        if pos.status == 'ACTIVE':
            pos.calc(trade)
            if not pos.trailing and pos.pl_pct <= -stop_pct:
                logging.info('Close position by stop-loss @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
                pos.close()
                if pos.amount > 0:
                    sell_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
                    sell_value.append(candle.close)
                else:
                    buy_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
                    buy_value.append(candle.close)
            if pos.pl_pct >= trailing_profit_pct and not pos.trailing:
                pos.trailing_stop(trailing_stop_pct)
            if pos.status != "CLOSED" and pos.trailing:
                pos.trailing_stop(trailing_stop_pct)
        if pos.status == "CLOSED":
            if pos.trailing:
                logging.info('Close position by trailing @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
            if pos.amount > 0:
                sell_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
                sell_value.append(candle.close)
            else:
                buy_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
                buy_value.append(candle.close)
            pl += pos.pl
            pl_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
            pl_value.append(pl)
            logging.info('PL: ' + str(pl))
            positions.append(pos)
            pos = Position()
        candle = OHLCV()
        #     # logging.info(last_signal + '->' + strategy.signal + ':' + str(trade['price']))
        #     # print(last_signal, '->', strategy.signal)
        #     # Open long position
        #     if strategy.signal == 'buy' and pos.status != 'ACTIVE' and trade['price'] != 0:
        #         logging.info('Open long position @ ' + str(trade['price']) + " length: " + str(strategy.length))
        #         pos.open('btcusd', float(trade['price']), margin / float(trade['price']))
        #         # Set target and stop loss
        #         # trailing_profit_pct = strategy.up_percent / 2
        #         # stop_pct = trailing_profit_pct
        #         buy_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        #         buy_value.append(candle.close)
        #     # Open short position
        #     if strategy.signal == 'sell' and pos.status != 'ACTIVE' and trade['price'] != 0:
        #         logging.info('Open short position @ ' + str(trade['price']) + " length: " + str(strategy.length))
        #         pos.open('btcusd', float(trade['price']), -margin / float(trade['price']))
        #         # Set target and stop loss
        #         # trailing_profit_pct = strategy.down_percent / 2
        #         # stop_pct = trailing_profit_pct
        #         sell_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        #         sell_value.append(candle.close)
        #     last_signal = strategy.signal
        # # Calculate position P/L
        # if pos.status == 'ACTIVE':
        #     pos.calc(trade)
        #     # if not pos.trailing and (pos.pl_pct <= -stop_pct
        #     #                          or (strategy.signal == 'sell' and pos.amount > 0)
        #     #                          or (strategy.signal == 'buy' and pos.amount < 0)):
        #     if not pos.trailing and pos.pl_pct <= -stop_pct:
        #         logging.info('Close position by stop-loss @ ' + str(trade['price']) + ' @ ' +
        #                      str(pos.pl_pct) if pos.pl_pct <= -stop_pct
        #                      else 'Close position by signal @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
        #         pos.close()
        #         if pos.amount > 0:
        #             sell_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        #             sell_value.append(candle.close)
        #         else:
        #             buy_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        #             buy_value.append(candle.close)
        #     if pos.pl_pct >= trailing_profit_pct and not pos.trailing:
        #         pos.trailing_stop(trailing_stop_pct)
        #     if pos.status != "CLOSED" and pos.trailing:
        #         pos.trailing_stop(trailing_stop_pct)
        #     if pos.status == "CLOSED":
        #         if pos.trailing:
        #             logging.info('Close position by trailing @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
        #         if pos.amount > 0:
        #             sell_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        #             sell_value.append(candle.close)
        #         else:
        #             buy_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        #             buy_value.append(candle.close)
        #         pl += pos.pl
        #         pl_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        #         pl_value.append(pl)
        #         logging.info('PL: ' + str(pl))
        #         positions.append(pos)
        #         pos = Position()
        # candle = OHLCV()

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
fee = len(positions) * margin * 0.003
print('Profit:', profit - fee)
print('ROI%: ', (profit - fee) / margin * 100)
# print(len(buy_value), len(sell_value), len(buy_index), len(sell_index))
plt.plot(price_index, price_value, 'b-', label='Price')
plt.plot(pl_index, pl_value, 'r-', label='Price')
plt.plot(buy_index, buy_value, '^', markersize=10, color='g', label='Buy')
plt.plot(sell_index, sell_value, 'v', markersize=10, color='r', label='Sell')
plt.ylabel('USD')
plt.xlabel('Date')
plt.legend(loc=0)
plt.show()
# print('Max trading fee (taker):', fee)
# for candle in candle_list:
#     print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
