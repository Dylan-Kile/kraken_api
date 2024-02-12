import trade_analyzer
from trade_handler import TradeHandler
from trade_analyzer import get_current_value_of_ticker, get_current_value_of_trades
from trade_finder import add_based_on_avg_volume, add_based_on_spread
from datetime import date

from kraken_api.kraken_client import KrakenClient


def get_current_value_of_trades():
    trade_handler = TradeHandler()
    open_trades = trade_handler.get_open_trades()
    closed_trades = trade_handler.get_closed_trades()

    return trade_analyzer.get_current_value_of_trades(
        open_trades, closed_trades, trade_handler.columns
    )


if __name__ == "__main__":
    client = KrakenClient()
    prompt = """Please select an option:
      (a) book a trade
      (b) fetch current prices
      (c) check candle data for a ticker
    """
    while (choice := input(prompt)) not in set(["a", "b", "c"]):
        continue

    if choice == "a":
        trade_handler = TradeHandler()

        num_to_add = int(input("Please enter how many trades you want to add. "))
        while num_to_add > 0:
            coin = input("Please enter the coin pairing. ")
            while (
                eventType := input(
                    "Please enter the eventType. Please only enter BUY or SELL. "
                )
            ) not in set(["BUY", "SELL"]):
                continue
            while (
                positionType := input(
                    "Please enter the positionType. Please only enter SHORT or LONG. "
                )
            ) not in set(["SHORT", "LONG"]):
                continue
            current_date = date.today()
            date_input = input(
                f"Please enter the datetime. Press Enter to default to current date ({current_date.isoformat()})"
            )
            if date_input == "":
                date_input = current_date.isoformat()

            current_amount = get_current_value_of_ticker(coin[:-4])
            amount = input(
                f"Please enter the amount. Press Enter to default to current amount ({current_amount})"
            )
            if amount == "":
                amount = current_amount
            amount = float(amount)

            quantity = float(input("Please enter amount spent in USD. ")) / amount

            trade_handler.add_trade(
                coin, eventType, positionType, date_input, amount, quantity
            )

            num_to_add -= 1
    elif choice == "b":
        get_current_value_of_trades()
    else:
        ticker = input(
            "Please enter the ticker you want to get candle data for. Example (SUPER/USD) "
        )

        candles = client.get_candle_data_for_ticker("SUPER/USD")
        print(24 * add_based_on_avg_volume(candles))
