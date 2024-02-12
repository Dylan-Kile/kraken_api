import os
import csv
import time

import requests

API_PATH = "https://discord.com/api/v10"
CHANNELS_PATH = f"{API_PATH}/channels"


class DiscordBot:
    def get_bot_token():
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        with open(f"{cur_dir}/discord-bot-token.txt") as f:
            return f.readline()

    def get_channel_information():
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        with open(f"{cur_dir}/channels.csv") as channel_file:
            content = list(csv.DictReader(channel_file))
        return {row["name"]: row["id"] for row in content}

    def __init__(self):
        self.bot_token = DiscordBot.get_bot_token()
        self.channel_information = DiscordBot.get_channel_information()

    def get_nonce():
        return time.time_ns()

    def get_auth_header(self):
        return {"Authorization": f"Bot {self.bot_token}"}

    def send_basic_message(self, channel_name, message):
        body = {"content": message}
        self._send_message(channel_name, body)

    def _send_message(self, channel_name, message):
        headers = self.get_auth_header() | {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        new_body = message | {"nonce": DiscordBot.get_nonce()}
        url = f"{CHANNELS_PATH}/{self.channel_information[channel_name]}/messages"

        requests.post(url, new_body, headers=headers)


if __name__ == "__main__":
    bot = DiscordBot()
    bot.send_basic_message("general", "Hi again.")
