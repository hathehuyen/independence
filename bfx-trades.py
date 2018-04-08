import websocket
import json
try:
    import thread
except ImportError:
    import _thread as thread
import time

length_ts = 3600
buys = []
sells = []
total_buy = 0
total_sell = 0


def on_message(ws, message):
    global buys
    global sells
    global total_buy
    global total_sell
    # print(message)
    mess = json.loads(message)
    if type(mess) is list:
        if mess[1] == 'te':
            # print(mess)
            if mess[-1] > 0:
                buys.append(mess)
                total_buy += mess[-1]
                while buys:
                    if buys[0][-3] + length_ts < time.time():
                        total_buy -= buys[0][-1]
                        buys.pop(0)
                    else:
                        break
            else:
                sells.append(mess)
                total_sell += mess[-1]
                while sells:
                    if sells[0][-3] + length_ts < time.time():
                        total_sell -= sells[0][-1]
                        sells.pop(0)
                    else:
                        break
            print(len(buys), "Buy:", total_buy, " - ", len(sells), "Sell:", total_sell, "@", mess[-2])


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    def run(*args):
        ws.send('{"event": "subscribe", "channel": "trades", "symbol": "tBTCUSD"}')
    thread.start_new_thread(run, ())


if __name__ == "__main__":
    # websocket.enableTrace(True)
    while True:
        ws = websocket.WebSocketApp("wss://api.bitfinex.com/ws",
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.on_open = on_open
        ws.run_forever()
        time.sleep(1)

