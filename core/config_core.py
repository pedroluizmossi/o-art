import configparser
import os

_CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT_DIR = os.path.dirname(_CURRENT_SCRIPT_DIR)
config_file_path = os.path.join(_PROJECT_ROOT_DIR, "config.ini")


class Config:
    """
    A class to manage configuration settings for the application.

    Attributes:
        config (ConfigParser): The ConfigParser object to read and write configuration files.
        config_file (str): The path to the configuration file.
    """

    def __init__(self, config_file=config_file_path):
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
            self.server_address = self.config_instance.get("ComfyUI", "server")

        def get_server_address(self):
            return self.server_address

    class Fief:
        def __init__(self, config_instance):
            self.config_instance = config_instance
            self.domain = self.config_instance.get("Fief", "domain")

        def get_domain(self):
            return self.domain

    class Logs:
        def __init__(self, config_instance):
            self.config_instance = config_instance
            self.level = self.config_instance.get("Logs", "level")
            self.path = self.config_instance.get("Logs", "path")
            self.max_files = int(self.config_instance.get("Logs", "max_files"))
            self.max_backups = int(self.config_instance.get("Logs", "max_backups"))

        def get_level(self):
            return self.level
        def get_path(self):
            return self.path
        def get_max_files(self):
            return self.max_files
        def get_max_backups(self):
            return self.max_backups

    class Redis:
        def __init__(self, config_instance):
            self.config_instance = config_instance
            self.host = self.config_instance.get("redis", "host", "localhost")
            self.port = int(self.config_instance.get("redis", "port", 6379))  # Convert to int

        def get_host(self):
            return self.host

        def get_port(self):
            return self.port

        def get_settings(self):
            # Helper method to return settings compatible with metrics
            from arq.connections import RedisSettings
            return RedisSettings(host=self.host, port=self.port)
