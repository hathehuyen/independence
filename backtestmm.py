#!/usr/bin/env python
import logging
import time
from db import *
from common.ohlcv import OHLCV
from common.indicators import MACD
from common.order import Order
from common.position import Position
# from strategies.volume_support_resistance import VolumeSupportResistance
from strategies.volume_based import VolumeBased
from strategies.retrace import Retrace
from strategies.extend import Extend
import matplotlib.pyplot as plt
from datetime import datetime

# Log config
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# Margin available
margin = 5000
start_margin = 100
# Candle length milisecond
# 5 seconds
# candle_period = 5000
candle_period = 60000
min_length = 60
max_length = 60
diff = 1
macd_short = 21
macd_long = 55
order_diff = 0.5
order_valid_time = 60000 * 60
# Back test data settings
selector = 'bitfinex.BTC-USD'
start = time.mktime(datetime.strptime('201712010000', "%Y%m%d%H%M%S").timetuple()) * 1000
end = time.mktime(datetime.strptime('201804302359', "%Y%m%d%H%M%S").timetuple()) * 1000

add_percent = 4
# Trailing stop percent
trailing_profit_pct = 5
trailing_stop_pct = 0.2
# Stop loss percent
stop_pct = 5

# print(start, end)


# Get trades data from db
trade_cursor = trades.find({"selector": selector, "time": {"$lte": end, "$gte": start}}).sort([("time", 1)])
# Back testing
candle = OHLCV()
macd = MACD(macd_short, macd_long)
strategy = Extend(min_len=min_length, max_len=max_length, diff=diff)
order = None
pos = Position()
positions = []
last_signal = None
pl = 0
plot_price_index = []
plot_price_value = []
plot_buy_index = []
plot_buy_value = []
plot_sell_index = []
plot_sell_value = []
plot_pl_index = []
plot_pl_value = []
plot_macd_short = []
plot_macd_long = []


def check_position(candle: OHLCV, trade):
    # Check position status
    global margin
    global pos
    global pl
    global plot_sell_index
    global plot_sell_value
    global plot_buy_index
    global plot_buy_value
    global plot_pl_index
    global plot_pl_value
    if pos.status == 'ACTIVE':
        pos.calc(trade)
        if pos.pl_pct <= -add_percent and abs(pos.amount * pos.base) < margin:
            pos.add(trade['price'], pos.amount)
            pos.calc(trade)
        if not pos.trailing and pos.pl_pct <= -stop_pct:
            pos.close()
        if pos.pl_pct >= trailing_profit_pct and not pos.trailing:
            pos.trailing_stop(trailing_stop_pct)
        if pos.status != "CLOSED" and pos.trailing:
            pos.trailing_stop(trailing_stop_pct)
    if pos.status == "CLOSED":
        if pos.trailing:
            logging.info('Close position by trailing @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
        else:
            logging.info('Close position by stop-loss @ ' + str(trade['price']) + ' @ ' + str(pos.pl_pct))
        if pos.amount > 0:
            plot_sell_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
            plot_sell_value.append(candle.close)
        else:
            plot_buy_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
            plot_buy_value.append(candle.close)
        pl += pos.pl - (pos.fee * 2)
        plot_pl_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        plot_pl_value.append(pl)
        logging.info('PL: ' + str(pl))
        positions.append(pos)
        if pos.amount * pos.base > margin:
            margin = pos.amount * pos.base
        pos = Position()


for trade in trade_cursor:
    # Add trade to OHLCV candle
    candle.add_trade(trade['time'], trade['size'], trade['price'], trade['side'])
    # print(candle.start, candle.end, candle.open, candle.high, candle.low, candle.close, candle.volume)
    # Complete one OHCLV candle
    if candle.start != 0 and candle.end != 0 and candle.end - candle.start >= candle_period:
        plot_price_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
        plot_price_value.append(candle.close)
        # Add candle to strategy
        strategy.add_candle(candle)
        # vb_strategy.add_candle(candle)
        macd.add_candle(candle)
        plot_macd_long.append(macd.ma_long)
        plot_macd_short.append(macd.ma_short)
        # We got a new signal that difference from last signal => open an order
        # if macd.macd and strategy.signal != last_signal and (
        #         (strategy.signal == 'buy' and macd.macd > 0) or (strategy.signal == 'sell' and macd.macd < 0)
        # ):
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
                    pos.open('btcusd', order.price, start_margin / float(order.price))
                    plot_buy_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
                    plot_buy_value.append(order.price)
                if order.side == 'sell':
                    logging.info('Open short position @ ' + str(order.price) + " diff: " + str(strategy.down_percent * 100))
                    pos.open('btcusd', order.price, -start_margin / float(order.price))
                    plot_sell_index.append(datetime.fromtimestamp(float(candle.start / 1000)))
                    plot_sell_value.append(order.price)
                # trailing_profit_pct = (strategy.down_percent * 100 + order_diff) / 4
                # stop_pct = trailing_profit_pct * 2
                order = None
            elif order.status == 'CANCELED':
                order = None
        check_position(candle, trade)
        candle = OHLCV()

if pos.status == 'ACTIVE':
    positions.append(pos)
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
print('Profit:', profit)
print('ROI%: ', profit / margin * 100)
print('Max margin used: ', margin)
# print(len(buy_value), len(sell_value), len(buy_index), len(sell_index))
plt.plot(plot_price_index, plot_price_value, 'b-', label='Price')
plt.plot(plot_price_index, plot_macd_short, 'g-', label='MA12')
plt.plot(plot_price_index, plot_macd_long, 'y-', label='MA26')
plt.plot(plot_pl_index, plot_pl_value, 'r-', label='Profit')
plt.plot(plot_buy_index, plot_buy_value, '^', markersize=10, color='g', label='Buy')
plt.plot(plot_sell_index, plot_sell_value, 'v', markersize=10, color='r', label='Sell')
plt.ylabel('USD')
plt.xlabel('Date')
plt.legend(loc=0)
plt.show()
