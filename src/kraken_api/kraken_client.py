import base64
import csv
import hashlib
import hmac
from typing import List
import pyotp
import time
import requests
import json
from threading import Thread
from importlib import resources

import urllib
from kraken_api.configuration.kraken_config import KrakenConfiguration
from datetime import datetime
from kraken_api.model.interval import TradeInterval
from kraken_api.model.trade_history_record import TradeHistoryRecord

from kraken_api.paths.kraken_api_paths import KrakenPaths

from kraken_api.model.candle import Candle
from kraken_api.model.ticker import Ticker
from queue import PriorityQueue

from kraken_api.model.api_action import ApiAction
from kraken_api.paths.request_type import RequestType


class KrakenClient:
    API_LIMIT = 15

    def __init__(self, config: KrakenConfiguration):
        self.api_counter = 0
        self.queue = PriorityQueue()
        self.config = config

        def decrement_counter():
            while True:
                while self.api_counter > 0:
                    self.api_counter = max(self.api_counter - 1, 0)
                    time.sleep(3)

        self.counter_thread: Thread = Thread(target=decrement_counter, daemon=True)
        self.counter_thread.start()

    def get_otp(self):
        totp = pyotp.TOTP(self.config.otp_secret)

        return totp.now()

    def get_nonce():
        return int(time.time() * 1000)

    def get_data_or_raise(response: requests.Response):
        if response.status_code != 200:
            raise Exception(f"{response.status_code} found: {str(response.content)}")
        response_info = json.loads(response.content)
        if len(response_info["error"]) > 0:
            raise Exception(response_info["error"])
        else:
            return response_info["result"]

    def handle_error(error) -> ApiAction:
        if "EGeneral:Internal error" in error:
            return (ApiAction.Retry, error)
        else:
            return (ApiAction.Abort, error)

    def api_call(api_func):
        def new_call(
            self,
            path: KrakenPaths,
            params={},
            payload={},
        ):
            self.api_counter += path.cost_to_call

            result = api_func(self, path, params, payload)

            return result

        return new_call

    def get_exclusions():
        with resources.files("local_files").joinpath(
            "excluded_pairs_in_us.csv"
        ).open() as exclusions_file:
            return set(row["ticker"] for row in csv.DictReader(exclusions_file))

    def get_authorization_headers(self, uri_path, payload):
        if not self.config.api_private_key or not self.config.api_key:
            raise Exception(
                "To perform private calls, please provide your API Key as well as your Secret key"
            )

        postdata = urllib.parse.urlencode(payload)
        encoded = (str(payload["nonce"]) + postdata).encode()
        message = uri_path.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(
            base64.b64decode(self.config.api_private_key), message, hashlib.sha512
        )
        sigdigest = base64.b64encode(mac.digest())

        return {
            "API-Sign": sigdigest.decode(),
            "API-Key": self.config.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def get_initial_private_payload(self):
        payload = {
            "nonce": KrakenClient.get_nonce(),
        }
        if self.config.otp_secret:
            payload.otp = self.get_otp()

        return payload

    @api_call
    def perform_request(self, path: KrakenPaths, params={}, payload={}):
        headers = {
            "User-Agent": "Python API Client",
        }
        if path.request_type == RequestType.Private:
            payload = payload | self.get_initial_private_payload()
            headers = headers | self.get_authorization_headers(path.path, payload)

        if path.http_method == "GET":
            return KrakenClient.get_data_or_raise(
                requests.get(path.uri, params=params, headers=headers)
            )
        elif path.http_method == "POST":
            return KrakenClient.get_data_or_raise(
                requests.post(path.uri, params=params, data=payload, headers=headers)
            )

    def get_open_trades(self):
        return self.perform_request(KrakenPaths.OPEN_ORDERS_PATH)

    def get_trade_history(
        self, start=0.0, end=time.time(), offset=0
    ) -> List[TradeHistoryRecord]:
        payload = {
            "start": start,
            "end": end,
            "ofs": offset,
            "consolidate_taker": False,
        }
        data = self.perform_request(KrakenPaths.TRADES_HISTORY_PATH, payload=payload)

        trades = data["trades"].values()
        for trade in trades:
            if trade["pair"] == "XXMRZUSD":
                print(",".join(str(v) for v in trade.values()))
        return [
            TradeHistoryRecord(
                trade["time"],
                trade["pair"],
                trade["type"],
                float(trade["price"]),
                (
                    float(trade["vol"])
                    * (
                        1
                        if trade["type"] == "sell"
                        else 1 - float(trade["fee"]) / float(trade["cost"])
                    )
                ),
            )
            for trade in trades
        ]

    def get_open_positions(self):
        return self.perform_request(KrakenPaths.OPEN_POSITIONS_PATH)

    def get_tickers(self):
        data = self.perform_request(KrakenPaths.TICKER_INFO_PATH)

        exclusions = KrakenClient.get_exclusions()
        return [
            ticker_pair
            for ticker_pair in data.keys()
            if ticker_pair.endswith("USD") and ticker_pair not in exclusions
        ]

    def get_ticker_data(self):
        data = self.perform_request(KrakenPaths.TICKER_INFO_PATH)

        exclusions = KrakenClient.get_exclusions()
        return [
            Ticker(
                ticker,
                entry["a"],
                entry["b"],
                entry["c"],
                entry["v"],
                entry["p"],
                entry["t"],
                entry["l"],
                entry["h"],
                entry["o"],
            )
            for (ticker, entry) in data.items()
            if ticker.endswith("USD") and ticker not in exclusions
        ]

    def get_candle_data_for_ticker(
        self, ticker, days_back=14, interval=TradeInterval.ONE_HOUR
    ):
        cur_time = datetime.now().timestamp()
        interval_in_seconds = interval.value / 60
        adjusted_cur_time = int((cur_time // interval_in_seconds) * interval_in_seconds)

        since = adjusted_cur_time - days_back * 86400
        data = self.perform_request(
            KrakenPaths.CANDLE_INFO_PATH,
            params={
                "pair": ticker.replace("/", ""),
                "interval": interval.value,
                "since": since,
            },
        )
        response_data = data[ticker.replace("/", "")]

        return [Candle(*row) for row in response_data]
