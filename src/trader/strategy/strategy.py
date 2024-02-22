from typing import Callable, List

from kraken_api.model.candle import Candle
from kraken_api.model.ticker import Ticker


class StrategyNode:
    def __init__(self, strategy: Callable[[List[Candle]], bool]):
        self.strategy = strategy
        self.depends_on: List[StrategyNode] = []

    def add_dependency(self, strategy_node):
        self.depends_on.append(strategy_node)

    def satisfies_dependencies(self, candles: List[Candle]):
        return all(strategy_node.strategy(candles) for strategy_node in self.depends_on)

    def __str__(self):
        str_repr = ""
        if len(self.depends_on) > 0:
            str_repr += f"[{','.join(strategy_node.strategy.__name__ for strategy_node in self.depends_on)}] -> "

        str_repr += self.strategy.__name__

        return str_repr

    def __repr__(self):
        return str(self)

    def execute(self, candles: List[Candle]) -> bool:
        return self.satisfies_dependencies(candles) and self.strategy(candles)


strategy_node_lookup = {}
strategies: List[StrategyNode] = []
delta_strategies: List[Callable[[Ticker, Ticker], bool]] = []
requirements = []


def add_strategy(strategy):
    if strategy.__name__ not in strategy_node_lookup:
        strategy_node = StrategyNode(strategy)
        strategy_node_lookup[strategy.__name__] = strategy_node

    strategies.append(strategy_node_lookup[strategy.__name__])

    return strategy


def add_requirement(requirement):
    requirements.append(requirement)

    return requirement


def depends_on(
    *strategy_dependencies: List[Callable[[Ticker, Ticker], tuple[bool, str]]]
):
    def wrapper(strategy):
        if strategy.__name__ not in strategy_node_lookup:
            strategy_node_lookup[strategy.__name__] = StrategyNode(strategy)

        strategy_node = strategy_node_lookup[strategy.__name__]
        for dependency in strategy_dependencies:
            if dependency.__name__ not in strategy_node_lookup:
                strategy_node_lookup[dependency.__name__] = StrategyNode(dependency)

            dependency_node = strategy_node_lookup[dependency.__name__]

            strategy_node.add_dependency(dependency_node)

        return strategy

    return wrapper


def add_delta_strategy(strategy: Callable[[Ticker, Ticker], tuple[bool, str]]):
    delta_strategies.append(strategy)

    return strategy
