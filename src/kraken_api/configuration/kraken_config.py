from importlib import resources
import yaml


class KrakenConfiguration:
    def __init__(self, api_private_key=None, api_key=None, otp_secret=None):
        self.api_private_key = api_private_key
        self.api_key = api_key
        self.otp_secret = otp_secret

    def read_from_resource_file(package, file_name):
        with resources.files(package).joinpath(file_name).open("r") as config_resource:
            return KrakenConfiguration(
                **yaml.safe_load(config_resource)["config"]["tokens"]
            )
    
    def __repr__(self):
        return f"api_private_key={self.api_private_key}, api_key={self.api_key}, otp_secret={self.otp_secret}"
