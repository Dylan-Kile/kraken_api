class TradeHistoryRecord:
    def __init__(self, timestamp, ticker, type, cost, fee, price, quantity):
        self.timestamp: float = timestamp
        self.ticker = ticker
        self.type = type
        self.cost: float = cost
        self.fee: float = fee
        self.price: float = price
        self.quantity: float = quantity

    def __str__(self) -> str:
        return f"[timestamp={self.timestamp}, ticker={self.ticker}, type={self.type}, cost={self.cost}, fee={self.fee}, price={self.price}, quantity={self.quantity}]"

    def __repr__(self):
        return str(self)
