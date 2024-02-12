import csv
from datetime import date
from typing import List

from model.trade import Trade
from functools import reduce
from itertools import chain
from collections import defaultdict

FILE_PATH = 'local/transaction_data.csv'


class TradeHandler:

    def __init__(self):
        with open(FILE_PATH) as f:
            reader = csv.DictReader(f)
            self.trades = list(Trade(row['batch'], row['coin'], row['eventType'],
                               row['positionType'],row['date'], float(row['amount']), float(row['quantity'])) for row in reader)
            self.columns = list(reader.fieldnames)

    def get_trades_for_coin_pair(self, coin_pair):
        return [trade for trade in self.get_open_trades() if trade.coin == coin_pair]
    
    def get_new_batch(self):
        return max(int(trade.batch) for trade in self.trades) + 1
        
    def add_trade(self, coin, eventType, positionType, date, amount, quantity):
        coin_pair = coin
        existing_trades = self.get_trades_for_coin_pair(coin_pair)
        if len(existing_trades) > 0:
            batch = existing_trades[0].batch
        else:
            batch = self.get_new_batch()
        with open(FILE_PATH, 'a') as out:
            dict_writer = csv.DictWriter(out, self.columns)
            dict_writer.writerow({
                'batch': batch,
                'coin': coin,
                'eventType': eventType,
                'positionType': positionType,
                'date': date,
                'amount': amount,
                'quantity': quantity
            })
    
    def get_open_trades(self):
        return self.get_trades_with_criteria(lambda values: not any([trade.eventType == 'SELL' for trade in values]))
    
    def get_closed_trades(self) -> List[Trade]:
        return self.get_trades_with_criteria(lambda values: any([trade.eventType == 'SELL' for trade in values]))
    
    def get_trades_with_criteria(self, criteria_for_trade_func):
        def reduction_function(accumulator, element: Trade):
            accumulator[(element.batch, element.positionType)].append(element)

            return accumulator
        
        trades_by_batch = reduce(reduction_function, self.trades, defaultdict(list))
        
        return list(chain.from_iterable([values for values in trades_by_batch.values() if criteria_for_trade_func(values)]))
        