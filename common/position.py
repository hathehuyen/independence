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

    def trailing_stop(self, percent: float = 0):
        self.trailing = True
        if self.last_pl_pct == 0:
            self.last_pl_pct = self.pl_pct
        elif self.pl_pct > self.last_pl_pct:
            self.last_pl_pct = self.pl_pct
        elif self.last_pl_pct - self.pl_pct >= percent:
            self.close()
