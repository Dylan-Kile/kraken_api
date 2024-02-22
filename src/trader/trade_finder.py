from statistics import mean
import csv
import time
import logging
from typing import List, Set
from threading import Thread
from kraken_api.kraken_client import KrakenClient
from kraken_api.configuration.kraken_config import KrakenConfiguration
from trader.strategy.strategy import (
    add_delta_strategy,
    add_requirement,
    add_strategy,
    depends_on,
    strategies,
    requirements,
    delta_strategies,
)
from importlib import resources
from collections import defaultdict

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
    return ticker.volume.past_24_hrs * ticker.high.past_24_hrs > 2000000


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


def higher_than_avg_volume(candles: List[Candle]):
    num_intervals = 24 * 5
    avg_volume = mean(candle.volume for candle in candles[-num_intervals:-1])

    return candles[-1].volume > avg_volume * 1.05


# @add_strategy
# def low_volume_but_high_price_movement(candles: List[Candle]):
#     num_intervals = 24 * 5
#     avg_volume = mean(candle.volume for candle in candles[-num_intervals:])

#     cur_candle = candles[-1]
#     high_price_requirement = 0.005
#     result = (
#         cur_candle.volume < 0.9 * avg_volume
#         and abs(cur_candle.close / cur_candle.open - 1) >= high_price_requirement
#     )

#     return result


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
@depends_on(higher_than_avg_volume)
def gap(candles: List[Candle]):
    prev_candle, cur_candle = candles[-2], candles[-1]

    return (
        cur_candle.open > prev_candle.close
        and not prev_candle.is_red()
        and not cur_candle.is_red()
    )


@add_strategy
def is_within_threshold_to_support(candles: List[Candle]):
    stack = []
    prev = candles[0]
    for current_candle in candles[1:-1]:
        if (prev.is_red() and not current_candle.is_red()) or (
            not prev.is_red() and current_candle.is_red()
        ):
            close = min(prev.close, current_candle.close)
            while len(stack) > 0 and stack[-1] > close:
                stack.pop()
            stack.append(close)
        prev = current_candle

    for close in stack:
        if abs(candles[-1].close - close) < 0.1 * (candles[-1].high - candles[-1].low):
            return True


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
        logging.info("Evaluating strategies")
        for ticker in tickers:
            candle_data = kraken_client.get_candle_data_for_ticker(ticker)
            results = [
                (strategy, strategy.execute(candle_data)) for strategy in strategies
            ]
            successes = [result for result in results if result[1]]

            if (
                len(successes) > 0
                and previous_successful_strategies.get(ticker, []) != successes
            ):
                logging.info(f"Found successful strategies for {ticker}")
                discord_bot.send_basic_message(
                    "strategies",
                    f"{ticker} - {len(successes)} strategies in place - {[result[0] for result in successes]}",
                )

            previous_successful_strategies[ticker] = successes

        time.sleep(300)


@add_delta_strategy
def significant_rate_of_change_in_volume_with_bullish_trajectory(
    prev: Ticker, cur: Ticker
):
    diff = cur.volume.today - prev.volume.today

    is_successful = (
        prev.volume.today != 0
        and diff != 0
        and diff / prev.volume.today > 0.05
        and cur.last_trade_closed.price > prev.last_trade_closed.price
    )
    if not is_successful:
        return (is_successful, None)
    else:
        return (
            is_successful,
            f"Percent change for volume of {100*diff / prev.volume.today:.4f}%",
        )


def transform_ticker_data(ticker_data: List[Ticker], tickers_in_scope: Set[str]):
    return {
        ticker.ticker: ticker
        for ticker in ticker_data
        if ticker.ticker in tickers_in_scope
    }


def perform_delta_strategies(
    kraken_client: KrakenClient, discord_bot: DiscordBot, tickers_in_scope: Set[str]
):
    interval = 30
    previous_tickers = transform_ticker_data(
        kraken_client.get_ticker_data(), tickers_in_scope
    )
    time.sleep(interval)
    while True:
        logging.info("Evaluating delta strategies")
        current_tickers = transform_ticker_data(
            kraken_client.get_ticker_data(), tickers_in_scope
        )

        for ticker_name, cur_ticker in current_tickers.items():
            prev_ticker = previous_tickers.get(ticker_name, None)
            if not prev_ticker:
                logging.error(f"{ticker_name} has no previous ticker")
                continue

            results = [
                (delta_strategy.__name__, delta_strategy(prev_ticker, cur_ticker))
                for delta_strategy in delta_strategies
            ]
            successes = [result for result in results if result[1][0]]
            if len(successes) > 0:
                logging.info(
                    f"Found successful delta strategies for {cur_ticker.ticker}"
                )
                discord_bot.send_basic_message(
                    "delta-strategies",
                    f"{cur_ticker.ticker} - {len(successes)} delta strategies in place - {[f'{result[0]}: {result[1][1]}' for result in successes]}",
                )

        previous_tickers = current_tickers
        time.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
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

    strategy_thread = Thread(
        target=perform_strategies, args=[kraken_client, discord_bot, tickers]
    )
    strategy_thread.start()

    delta_strategies_thread = Thread(
        target=perform_delta_strategies, args=[kraken_client, discord_bot, tickers]
    )
    delta_strategies_thread.start()
    # perform_strategies(kraken_client, discord_bot, tickers)
