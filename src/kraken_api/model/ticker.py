from collections import namedtuple

Ask = namedtuple("Ask", ["price", "whole_lot_volume", "lot_volume"])
Bid = namedtuple("Bid", ["price", "whole_lot_volume", "lot_volume"])
LastTradeClosed = namedtuple("LastTradeClosed", ["price", "lot_volume"])
Volume = namedtuple("Volume", ["today", "past_24_hrs"])
VolumeWeightedAvg = namedtuple("VolumeWeightedAvg", ["today", "past_24_hrs"])
NumTrades = namedtuple("NumTrades", ["today", "past_24_hrs"])
Low = namedtuple("Low", ["today", "past_24_hrs"])
High = namedtuple("High", ["today", "past_24_hrs"])


class Ticker:
    def convert_to_float(arr):
        return [float(e) for e in arr]

    def __init__(
        self,
        ticker,
        ask_arr,
        bid_arr,
        last_trade_closed_arr,
        volume_arr,
        volume_weighted_avg_price_arr,
        num_trades_arr,
        low_arr,
        high_arr,
        open_price,
    ):
        self.ticker = ticker
        self.ask = Ask(*Ticker.convert_to_float(ask_arr))
        self.bid = Bid(*Ticker.convert_to_float(bid_arr))
        self.last_trade_closed = LastTradeClosed(
            *Ticker.convert_to_float(last_trade_closed_arr)
        )
        self.volume = Volume(*Ticker.convert_to_float(volume_arr))
        self.volume_weighted_avg_price = VolumeWeightedAvg(
            *Ticker.convert_to_float(volume_weighted_avg_price_arr)
        )
        self.num_trades = NumTrades(*Ticker.convert_to_float(num_trades_arr))
        self.low = Low(*Ticker.convert_to_float(low_arr))
        self.high = High(*Ticker.convert_to_float(high_arr))
        self.open_price = float(open_price)

    def __str__(self):
        return (
            f"Market Data for {self.ticker}: \n"
            f"Ask: {self.ask}\n"
            f"Bid: {self.bid}\n"
            f"Last Trade Closed: {self.last_trade_closed}\n"
            f"Volume: {self.volume}\n"
            f"Volume Weighted Avg Price: {self.volume_weighted_avg_price}\n"
            f"Number of Trades: {self.num_trades}\n"
            f"Low: {self.low}\n"
            f"High: {self.high}\n"
            f"Open Price: {self.open_price}\n"
        )
