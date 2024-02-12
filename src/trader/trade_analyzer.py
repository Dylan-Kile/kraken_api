from statistics import mean
import csv
import itertools
from kraken_api.kraken_client import KrakenClient


class TradeAnalyzer:
    def __init__(self, kraken_client: KrakenClient):
        self.kraken_client = kraken_client


def calculate_gain_loss(bought_value, position_type, cur_value):
    if position_type == "LONG":
        return (cur_value / bought_value) - 1
    else:
        return (bought_value - cur_value) / bought_value


def get_current_value_of_ticker(self, coin):
    return self.kraken_client.get_ticker_lookup()[coin]


def get_current_value_of_trades(self, open_trades, closed_trades, columns):
    current_ticker_lookup = self.kraken_client.get_ticker_lookup()

    with open("local/cur_val_data.csv", "w") as out:
        columns = [c for c in columns]
        columns.extend(
            ["curValue", "unrealizedPercentGainLoss", "realizedPercentGainLoss"]
        )

        writer = csv.DictWriter(out, columns)
        writer.writeheader()
        for trade in open_trades:
            ticker = trade.coin.split("/")[0]
            cur_value = current_ticker_lookup[ticker]

            writer.writerow(
                {
                    "batch": trade.batch,
                    "coin": trade.coin,
                    "eventType": trade.eventType,
                    "positionType": trade.positionType,
                    "date": trade.date,
                    "amount": trade.amount,
                    "quantity": trade.quantity,
                    "curValue": cur_value,
                    "unrealizedPercentGainLoss": calculate_gain_loss(
                        float(trade.amount), trade.positionType, cur_value
                    ),
                }
            )

        closed_trades.sort(key=lambda a: (a.batch, a.eventType))
        for batch, trades_in_batch in itertools.groupby(
            closed_trades, key=lambda a: a.batch
        ):
            trades_by_event_type = [
                (event_type, list(trades))
                for event_type, trades in itertools.groupby(
                    trades_in_batch, key=lambda a: a.eventType
                )
            ]

            _, buys = trades_by_event_type[0]
            _, sells = trades_by_event_type[1]
            avg_buy_price = mean(buy.amount for buy in buys)
            avg_sell_price = mean(sell.amount for sell in sells)

            ticker = buys[0].coin.split("/")[0]
            position_type = buys[0].positionType
            cur_value = current_ticker_lookup[ticker]
            writer.writerow(
                {
                    "batch": batch,
                    "coin": ticker,
                    "positionType": position_type,
                    "date": max([trade.date for trade in sells]),
                    "realizedPercentGainLoss": calculate_gain_loss(
                        float(avg_buy_price), position_type, avg_sell_price
                    ),
                }
            )
