class Position(object):
    def __init__(self, symbol: str = 'btcusd', base: float = 0, amount: float = 0):
        """
        Position object used for back test simulation
        :param symbol:
        :param base:
        :param amount:
        """
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
        self.fee_pct = 0.2
        self.fee = 0

    def calc(self, trade):
        """
        Calculate profit/loss
        :param trade:
        :return:
        """
        if self.base != 0 and self.amount != 0:
            self.pl = trade['price'] * self.amount - self.base * self.amount - self.fee
            self.pl_pct = self.pl / abs(self.base * self.amount) * 100


    def add(self, price: float = 0, amount: float = 0):
        self.base = (self.base * self.amount + price * amount) / (self.amount + amount)
        self.amount += amount
        self.fee += abs(amount) * price * self.fee_pct / 100

    def open(self, symbol='btcusd', base: float = 0, amount: float = 0):
        """
        Open position
        :param symbol: btc/usd
        :param base: base price
        :param amount: amount
        :return: none
        """
        self.symbol = symbol
        self.status = 'ACTIVE'
        self.base = base
        self.amount = amount
        self.fee = abs(amount) * base * self.fee_pct / 100

    def close(self):
        """
        Close position
        :return: none
        """
        self.status = 'CLOSED'

    def trailing_stop(self, percent: float = 0):
        """
        Trailing stop: if profit reach target
        :param percent:
        :return:
        """
        self.trailing = True
        if self.last_pl_pct == 0:
            self.last_pl_pct = self.pl_pct
        elif self.pl_pct > self.last_pl_pct:
            self.last_pl_pct = self.pl_pct
        elif self.last_pl_pct - self.pl_pct >= percent:
            self.close()
