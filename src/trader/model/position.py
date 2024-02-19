class Position:
    def __init__(self, ticker, avg_price, quantity):
        self.ticker = ticker
        self.avg_price = avg_price
        self.quantity = quantity

    def __str__(self):
        return f"[ticker={self.ticker}, avg_price={self.avg_price}, quantity={self.quantity}]"

    def __repr__(self):
        return str(self)
