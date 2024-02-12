from importlib import resources
import yaml


class KrakenConfiguration:
    def __init__(self, api_key=None, secret_api_key=None, otp_secret=None):
        self.api_key = api_key
        self.secret_api_key = secret_api_key
        self.otp_secret = otp_secret

    def read_from_resource_file(package, file_name):
        with resources.files(package).joinpath(file_name).open("r") as config_resource:
            return yaml.safe_load(config_resource)
