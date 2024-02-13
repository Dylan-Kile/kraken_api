from enum import Enum

from kraken_api.paths.request_type import RequestType

BASE_HOST = "https://api.kraken.com"
PUBLIC_PATH = "/0/public"
PRIVATE_PATH = "/0/private"


class KrakenPaths(Enum):
    ASSET_INFO_PATH = f"{PUBLIC_PATH}/AssetPairs", RequestType.Public, "GET", 1
    TICKER_INFO_PATH = f"{PUBLIC_PATH}/Ticker", RequestType.Public, "GET", 1
    CANDLE_INFO_PATH = f"{PUBLIC_PATH}/OHLC", RequestType.Public, "GET", 2

    TRADES_HISTORY_PATH = (
        f"{PRIVATE_PATH}/TradesHistory",
        RequestType.Private,
        "POST",
        1,
    )
    OPEN_ORDERS_PATH = f"{PRIVATE_PATH}/OpenOrders", RequestType.Private, "POST", 1

    def __init__(self, path, request_type, http_method, cost_to_call):
        self.path = path
        self.uri = f"{BASE_HOST}{path}"
        self.request_type: RequestType = request_type
        self.http_method = http_method
        self.cost_to_call: float = cost_to_call
