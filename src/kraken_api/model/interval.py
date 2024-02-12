from enum import Enum

class TradeInterval(Enum):
    ONE_MINUTE = 1
    FIVE_MINUTES = 5
    FIFTEEN_MINUTES = 15
    THIRTY_MINUTES = 30
    ONE_HOUR = 60
    FOUR_HOUR = 240
    ONE_DAY = 1440
    ONE_WEEK = 10080
    FIFTEEN_DAYS = 21600
    