import configparser
import os


class ConfigReader:

    @staticmethod
    def read_config():
        config_path = os.path.join(os.path.dirname(__file__), "config.ini")
        config = configparser.ConfigParser()
        config.read(config_path)
        return config

    config = read_config()
