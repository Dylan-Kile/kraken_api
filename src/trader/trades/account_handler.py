from importlib import resources
import csv
import time
from typing import List
from kraken_api.configuration.kraken_config import KrakenConfiguration
from kraken_api.kraken_client import KrakenClient
from kraken_api.model.trade_history_record import TradeHistoryRecord
from trader.model.position import Position

HEADERS = ["timestamp", "ticker", "type", "cost", "fee", "price", "quantity"]


def get_open_transactions_from_disk() -> List[TradeHistoryRecord]:
    with resources.files("local_files").joinpath(
        "transactions.csv"
    ).open() as transaction_file:
        content = list(csv.DictReader(transaction_file))
    return [
        TradeHistoryRecord(
            float(row["timestamp"]),
            row["ticker"],
            row["type"],
            float(row["cost"]),
            float(row["fee"]),
            float(row["price"]),
            float(row["quantity"]),
        )
        for row in content
    ]


def update_disk_transactions(client: KrakenClient):
    current_transactions = get_open_transactions_from_disk()
    last_recorded_time = max(
        [transaction.timestamp for transaction in current_transactions] + [0]
    )

    now = time.time()
    offset = 0
    with resources.files("local_files").joinpath("transactions.csv").open(
        "a"
    ) as transaction_file:
        writer = csv.DictWriter(transaction_file, HEADERS)
        while (
            len(
                trade_records := client.get_trade_history(
                    last_recorded_time, now, offset
                )
            )
            != 0
            and max(record.timestamp for record in trade_records) > last_recorded_time
        ):
            writer.writerows(
                [
                    {
                        "timestamp": record.timestamp,
                        "ticker": record.ticker,
                        "cost": record.cost,
                        "fee": record.fee,
                        "type": record.type,
                        "price": record.price,
                        "quantity": record.quantity,
                    }
                    for record in trade_records
                    if record.timestamp > last_recorded_time
                ]
            )
            offset += 50


def get_current_positions(client: KrakenClient) -> List[Position]:

    trade_history_records = sorted(
        get_open_transactions_from_disk(), key=lambda record: record.timestamp
    )

    weighted_cost_by_ticker = {}
    for record in trade_history_records:
        total_cost, quantity = weighted_cost_by_ticker.get(record.ticker, (0, 0))
        if record.type == "buy":
            weighted_cost_by_ticker[record.ticker] = (
                total_cost + record.price * record.quantity,
                quantity + record.quantity,
            )
        else:
            weighted_cost_by_ticker[record.ticker] = (
                total_cost - total_cost * (record.quantity / quantity),
                quantity - record.quantity,
            )

    return [
        Position(ticker, total_cost / quantity, quantity)
        for ticker, (total_cost, quantity) in weighted_cost_by_ticker.items()
        if abs(quantity) > 0.01
    ]
