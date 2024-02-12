class Candle:
    def __init__(
        self,
        timestamp,
        open_price,
        high_price,
        low_price,
        close_price,
        vwap,
        volume,
        trades,
    ):
        self.timestamp = timestamp
        self.open = float(open_price)
        self.high = float(high_price)
        self.low = float(low_price)
        self.close = float(close_price)
        self.vwap = float(vwap)
        self.volume = float(volume)
        self.trades = int(trades)

    def __str__(self):
        return f"Candle(timestamp={self.timestamp}, open={self.open}, high={self.high}, low={self.low}, close={self.close}, vwap={self.vwap}, volume={self.volume}, trades={self.trades})"

    def __repr__(self) -> str:
        return str(self)

    def is_red(self) -> bool:
        return self.close < self.open
