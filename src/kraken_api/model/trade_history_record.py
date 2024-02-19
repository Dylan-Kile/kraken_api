class TradeHistoryRecord:
    def __init__(self, timestamp, ticker, type, price, quantity):
        self.timestamp: float = timestamp
        self.ticker = ticker
        self.type = type
        self.price: float = price
        self.quantity: float = quantity

    def __str__(self) -> str:
        return f"[timestamp={self.timestamp}, ticker={self.ticker}, type={self.type}, price={self.price}, quantity={self.quantity}]"

    def __repr__(self):
        return str(self)
