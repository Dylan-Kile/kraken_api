from typing import Callable, List

from kraken_api.model.candle import Candle
from kraken_api.model.ticker import Ticker


strategies: List[Callable[[List[Candle]], bool]] = []
delta_strategies: List[Callable[[Ticker, Ticker], bool]] = []
requirements = []


def add_strategy(strategy):
    strategies.append(strategy)

    return strategy


def add_requirement(requirement):
    requirements.append(requirement)

    return requirement


def add_delta_strategy(strategy: Callable[[Ticker, Ticker], tuple[bool, str]]):
    delta_strategies.append(strategy)

    return strategy
