from statistics import mean
import csv
import time
from typing import List
from kraken_api.kraken_client import KrakenClient
from kraken_api.configuration.kraken_config import KrakenConfiguration
from strategy.strategy import add_requirement, add_strategy, strategies, requirements
from importlib import resources

from kraken_api.kraken_client import KrakenClient
from kraken_api.model.candle import Candle
from discord_bot.discord_bot import DiscordBot
from kraken_api.model.ticker import Ticker


@add_requirement
def spread_between_highs_and_lows(ticker: Ticker):
    min_spread = 0.05
    if ticker.low.past_24_hrs == 0:
        return False
    rate_of_change = ticker.high.past_24_hrs / ticker.low.past_24_hrs
    return rate_of_change >= 1 + min_spread


@add_requirement
def avg_volume_greater_than_threshold(ticker: Ticker):
    return ticker.volume.past_24_hrs * ticker.high.past_24_hrs > 150000


@add_strategy
def bullish_engulfing(candles: List[Candle]):
    previous, current = candles[-3], candles[-2]
    return (
        previous.open < current.close
        and previous.close > current.open
        and previous.open > previous.close
    )


@add_strategy
def thrust(candles: List[Candle]):

    prev: Candle = candles[-3]
    cur: Candle = candles[-2]
    midpoint_of_prev = (prev.close + prev.open) / 2
    acceptable_range = 0.25 * (prev.open - prev.close)
    return (
        prev.is_red()
        and not cur.is_red()
        and (midpoint_of_prev - acceptable_range)
        <= cur.close
        <= (midpoint_of_prev + acceptable_range)
    )


@add_strategy
def hammer(candles: List[Candle]):
    last_candle = candles[-2]
    high_maximum = 0.01
    ratio_between_open_and_close_max = 0.01
    low_requirement = 0.03

    max_open_or_close = max(last_candle.open, last_candle.close)
    min_open_or_close = min(last_candle.open, last_candle.close)

    return (
        (max_open_or_close / min_open_or_close) - 1 <= ratio_between_open_and_close_max
        and (last_candle.high / max_open_or_close) - 1 <= high_maximum
        and (min_open_or_close / last_candle.low) - 1 >= low_requirement
    )


@add_strategy
def low_volume_but_high_price_movement(candles: List[Candle]):
    num_intervals = 24 * 5
    avg_volume = mean(candle.volume for candle in candles[-num_intervals:])

    cur_candle = candles[-1]
    high_price_requirement = 0.005
    result = (
        cur_candle.volume < 0.9 * avg_volume
        and abs(cur_candle.close / cur_candle.open - 1) >= high_price_requirement
    )

    return result


@add_strategy
def increased_volume_with_bullish_price_movement(candles: List[Candle]):
    num_intervals = 24 * 5
    avg_volume = mean(candle.volume for candle in candles[-num_intervals:])

    cur_candle = candles[-1]
    high_price_requirement = 0.01
    result = (
        cur_candle.volume >= 1.1 * avg_volume
        and cur_candle.close / cur_candle.open - 1 >= high_price_requirement
    )

    return result


@add_strategy
def gap(candles: List[Candle]):
    prev_candle, cur_candle = candles[-2], candles[-1]

    return (
        cur_candle.open > prev_candle.close
        and not prev_candle.is_red()
        and not cur_candle.is_red()
    )


def create_watchlist(kraken_client: KrakenClient):
    tickers_to_watch = []
    print("Creating watchlist")
    tickers = kraken_client.get_ticker_data()
    for ticker in tickers:
        if all(r(ticker) for r in requirements):
            tickers_to_watch.append(ticker)

    with resources.files("trader.local").joinpath("watchlist.csv").open("w") as out:
        out.write(
            "ticker\n" + "\n".join(sorted(ticker.ticker for ticker in tickers_to_watch))
        )


def perform_strategies(kraken_client: KrakenClient, discord_bot: DiscordBot, tickers):
    previous_successful_strategies = {}
    while True:
        for ticker in tickers:
            print(f"Evaluating strategies for {ticker}")
            candle_data = kraken_client.get_candle_data_for_ticker(ticker)
            results = [
                (strategy.__name__, strategy(candle_data)) for strategy in strategies
            ]
            successes = [result for result in results if result[1]]

            if (
                len(successes) > 0
                and previous_successful_strategies.get(ticker, []) != successes
            ):
                discord_bot.send_basic_message(
                    "strategies",
                    f"{ticker} - {len(successes)} strategies in place - {[result[0] for result in successes]}",
                )

            previous_successful_strategies[ticker] = successes

        time.sleep(300)


if __name__ == "__main__":
    kraken_client = KrakenClient(
        KrakenConfiguration.read_from_resource_file(
            "kraken_api.resources", "config.yaml"
        )
    )
    discord_bot = DiscordBot()
    create_watchlist(kraken_client)
    with resources.open_text("local", "watchlist.csv") as watchlist_file:
        watchlist = csv.DictReader(watchlist_file)
        tickers = [row["ticker"] for row in watchlist]

    perform_strategies(kraken_client, discord_bot, tickers)
