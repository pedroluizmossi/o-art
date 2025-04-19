# core/config_core.py (Corrigido)

import configparser
import os

_CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT_DIR = os.path.dirname(_CURRENT_SCRIPT_DIR)
DEFAULT_CONFIG_FILE_PATH = os.path.join(_PROJECT_ROOT_DIR, "config.ini")


class Config:
    """
    A simplified class to manage configuration settings from an INI file.
    """

    def __init__(self, config_file=DEFAULT_CONFIG_FILE_PATH):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self._load_config()  # Tornar privado para indicar uso interno

    def _load_config(self):
        """
        Load the configuration file. Logs an error if the file is not found.
        """
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
            except configparser.Error:
                self.config = configparser.ConfigParser()
        else:
            self.config = configparser.ConfigParser()

    def get(self, section, option, default=None):
        """
        Get a configuration value from the INI file.

        Args:
            section (str): The section of the configuration file.
            option (str): The option within the section.
            default: The default value to return if the section/option is not found.

        Returns:
            The value of the configuration option or the default value.
            Returns None if not found and no default.
        """
        return self.config.get(section, option, fallback=default)

    def getint(self, section, option, default=None):
        try:
            return self.config.getint(section, option, fallback=default)
        except (ValueError, TypeError):
            return default

    def getboolean(self, section, option, default=None):
        try:
            if not self.config.has_option(section, option):
                return default
            return self.config.getboolean(section, option)
        except (ValueError, TypeError):
            return default
