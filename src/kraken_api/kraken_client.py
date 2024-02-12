import base64
import csv
import hashlib
import hmac
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

from kraken_api.paths.kraken_api_paths import (
    ASSET_INFO_URI,
    CANDLE_INFO_URI,
    OPEN_ORDERS_PATH,
    OPEN_ORDERS_URI,
    TICKER_INFO_URI,
    TRADES_HISTORY_PATH,
    TRADES_HISTORY_URI,
)
from kraken_api.model.candle import Candle
from kraken_api.model.ticker import Ticker
from queue import PriorityQueue


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

    def api_call(time_increment=1):
        def wrapped_api_call(api_func):
            def new_call(self, *args, **kwargs):
                self.api_counter += time_increment

                result = api_func(self, *args, **kwargs)

                return result

            return new_call

        return wrapped_api_call

    def get_exclusions():
        with resources.files("local_files").joinpath(
            "excluded_pairs_in_us.csv"
        ).open() as exclusions_file:
            return set(row["ticker"] for row in csv.DictReader(exclusions_file))

    def get_authorization_headers(self, uri_path, payload):
        if not self.config.api_key or not self.config.secret_api_key:
            raise Exception(
                "To perform private calls, please provide your API Key as well as your Secret key"
            )

        postdata = urllib.parse.urlencode(payload)
        encoded = (str(payload["nonce"]) + postdata).encode()
        message = uri_path.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(
            base64.b64decode(self.config.secret_api_key), message, hashlib.sha512
        )
        sigdigest = base64.b64encode(mac.digest())

        return {
            "API-Sign": sigdigest.decode(),
            "API-Key": self.config.api_key,
            "User-Agent": "Python API Client",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def get_initial_private_payload(self):
        payload = {
            "nonce": KrakenClient.get_nonce(),
        }
        if self.config.otp_secret:
            payload.otp = self.get_otp()

        return payload

    @api_call()
    def get_open_trades(self):
        init_payload = self.get_initial_private_payload()
        headers = self.get_authorization_headers(OPEN_ORDERS_PATH, init_payload)

        response = requests.post(OPEN_ORDERS_URI, data=init_payload, headers=headers)

        return KrakenClient.get_data_or_raise(response)

    @api_call()
    def get_trade_history(self):
        init_payload = self.get_initial_private_payload()
        headers = self.get_authorization_headers(TRADES_HISTORY_PATH, init_payload)

        response = requests.post(TRADES_HISTORY_URI, data=init_payload, headers=headers)

        return KrakenClient.get_data_or_raise(response)

    @api_call()
    def get_tickers(self):
        response = requests.get(ASSET_INFO_URI)

        exclusions = KrakenClient.get_exclusions()
        return [
            ticker_pair
            for ticker_pair in KrakenClient.get_data_or_raise(response).keys()
            if ticker_pair.endswith("USD") and ticker_pair not in exclusions
        ]

    @api_call()
    def get_ticker_data(self):
        response = requests.get(TICKER_INFO_URI)

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
            for (ticker, entry) in KrakenClient.get_data_or_raise(response).items()
            if ticker.endswith("USD") and ticker not in exclusions
        ]

    @api_call(time_increment=2)
    def get_candle_data_for_ticker(
        self, ticker, days_back=14, interval=TradeInterval.ONE_HOUR
    ):
        cur_time = datetime.now().timestamp()
        interval_in_seconds = interval.value / 60
        adjusted_cur_time = int((cur_time // interval_in_seconds) * interval_in_seconds)

        since = adjusted_cur_time - days_back * 86400
        response = requests.get(
            CANDLE_INFO_URI,
            params={
                "pair": ticker.replace("/", ""),
                "interval": interval.value,
                "since": since,
            },
        )
        response_data = KrakenClient.get_data_or_raise(response)[
            ticker.replace("/", "")
        ]

        return [Candle(*row) for row in response_data]
