class Trade:
    def __init__(self, batch, coin, eventType, positionType, date, amount, quantity):
        self.batch = batch
        self.coin = coin
        self.eventType = eventType
        self.positionType = positionType
        self.date = date
        self.amount = amount
        self.quantity = quantity

    def __str__(self):
        return f"Trade(batch={self.batch}, coin={self.coin}, eventType={self.eventType}, positionType={self.positionType}, date={self.date}, amount={self.amount}, quantity={self.quantity})"
    
    def __repr__(self):
        return str(self)
