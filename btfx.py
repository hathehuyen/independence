
import logging
import time
import sys


from exchanges.bitfinex.btfxwss.btfxwss.client import BtfxWss

log = logging.getLogger(__name__)

# fh = logging.FileHandler('test.log')
# fh.setLevel(logging.DEBUG)
# sh = logging.StreamHandler(sys.stdout)
# sh.setLevel(logging.DEBUG)

# log.addHandler(sh)
# log.addHandler(fh)
# logging.basicConfig(level=logging.DEBUG, handlers=[fh, sh])


class Bitfinex(object):
    def __init__(self, base_url=None, symbol='BTCUSD', api_key=None, api_secret=None,
                 shouldWSAuth=True, postOnly=False, timeout=7):
        self.logger = logging.getLogger(__name__)
        self.ws = BtfxWss()
        self.apiKey = api_key
        self.apiSecret = api_secret
        self.ws.start()
        self.logger.info('Websocket connecting...')
        while not self.ws.conn.connected.is_set():
            time.sleep(1)
        self.logger.info('Websocket connected.')
        # Subscribe to some channels
        self.symbol = symbol
        self.ws.subscribe_to_ticker(symbol)
        self.ws.subscribe_to_order_book(symbol)

    def tickers(self):
        return self.ws.tickers(self.symbol)

# # Do something else
# t = time.time()
# while time.time() - t < 10:
#     pass
#
# # Accessing data stored in BtfxWss:
# ticker_q = wss.tickers('BTCUSD')  # returns a Queue object for the pair.
# while not ticker_q.empty():
#     print(ticker_q.get())
#
# # Unsubscribing from channels:
# wss.unsubscribe_from_ticker('BTCUSD')
# wss.unsubscribe_from_order_book('BTCUSD')
#
# # Shutting down the client:
# wss.stop()
