import threading
import time


class InMemoryStorage:
    def __init__(self, base_data_fetcher, refresh_rate=15):
        self.refresh_rate = refresh_rate
        self.stored_value = None

        def fetch_data():
            while True:
                self.stored_value = base_data_fetcher()

                time.sleep(refresh_rate)

        self.data_fetching_thread = threading.Thread(target=fetch_data)
        self.data_fetching_thread.start()
