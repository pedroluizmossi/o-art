import configparser
import os

config_file = "config.ini"

class Config:
    """
    A class to manage configuration settings for the application.

    Attributes:
        config (ConfigParser): The ConfigParser object to read and write configuration files.
        config_file (str): The path to the configuration file.
    """

    def __init__(self, config_file=config_file):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        """
        Load the configuration file.
        """
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            raise FileNotFoundError(f"The specified config file does not exist: {self.config_file}")

    def get(self, section, option, default=None):
        """
        Get a configuration value.

        Args:
            section (str): The section of the configuration file.
            option (str): The option within the section.
            default: The default value to return if the option is not found.

        Returns:
            The value of the configuration option or the default value.
        """
        try:
            return self.config.get(section, option)
        except configparser.NoOptionError:
            return default

    class Comfyui:
        def __init__(self, config_instance):
            self.config_instance = config_instance
            self.server_address = self.config_instance.get("ComfyUI", "server", "127.0.0.1:8188")

        def get_server_address(self):
            return self.server_address

    class Fief:
        def __init__(self, config_instance):
            self.config_instance = config_instance
            self.domain = self.config_instance.get("Fief", "domain", "http://127.0.0.1:8001")

        def get_domain(self):
            return self.domain

