import os

import yaml


class ConfigReader:

    @staticmethod
    def read_config():
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config

    config = read_config()
