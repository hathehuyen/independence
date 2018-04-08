import time
from btfx import Bitfinex

bfx = Bitfinex()
while True:
    time.sleep(5)
    print(bfx.tickers())
