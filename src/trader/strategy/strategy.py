from typing import Callable, List

from kraken_api.model.candle import Candle


strategies: List[Callable[[List[Candle]], bool]] = []
requirements = []


def add_strategy(strategy):
    strategies.append(strategy)

    return strategy


def add_requirement(requirement):
    requirements.append(requirement)

    return requirement
