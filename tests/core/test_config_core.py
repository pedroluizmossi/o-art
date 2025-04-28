# tests/test_config_core.py
import configparser
from unittest.mock import mock_open, patch

from core.config_core import Config

DEFAULT_CONFIG_CONTENT = """
[section1]
key1 = value1
key2 = 123
key3 = true
"""


def test_config_load_valid_file():
    with patch("builtins.open", mock_open(read_data=DEFAULT_CONFIG_CONTENT)), \
            patch("os.path.exists", return_value=True):
        config = Config("test_config.ini")
        value = config.get("section1", "key1")
        assert value == "value1"


def test_config_file_not_found():
    with patch("os.path.exists", return_value=False):
        config = Config("non_existent_config.ini")
        value = config.get("section1", "key1", default="default_value")
        assert value == "default_value"


def test_get_existing_key():
    with patch("builtins.open", mock_open(read_data=DEFAULT_CONFIG_CONTENT)), \
            patch("os.path.exists", return_value=True):
        config = Config("test_config.ini")
        value = config.get("section1", "key2")
        assert value == "123"


def test_get_nonexistent_key_with_default():
    with patch("builtins.open", mock_open(read_data=DEFAULT_CONFIG_CONTENT)), \
            patch("os.path.exists", return_value=True):
        config = Config("test_config.ini")
        value = config.get("section1", "key4", default="default_value")
        assert value == "default_value"


def test_getint_valid_value():
    with patch("builtins.open", mock_open(read_data=DEFAULT_CONFIG_CONTENT)), \
            patch("os.path.exists", return_value=True):
        config = Config("test_config.ini")
        value = config.getint("section1", "key2")
        assert value == 123


def test_getint_invalid_value():
    with patch("builtins.open", mock_open(read_data=DEFAULT_CONFIG_CONTENT)), \
            patch("os.path.exists", return_value=True):
        config = Config("test_config.ini")
        value = config.getint("section1", "key1", default=-1)
        assert value == -1


def test_getboolean_true_value():
    with patch("builtins.open", mock_open(read_data=DEFAULT_CONFIG_CONTENT)), \
            patch("os.path.exists", return_value=True):
        config = Config("test_config.ini")
        value = config.getboolean("section1", "key3")
        assert value is True


def test_getboolean_missing_value_with_default():
    with patch("builtins.open", mock_open(read_data=DEFAULT_CONFIG_CONTENT)), \
            patch("os.path.exists", return_value=True):
        config = Config("test_config.ini")
        value = config.getboolean("section1", "key4", default=False)
        assert value is False


def test_load_config_file_invalid_format():
    with patch("os.path.exists", return_value=True), \
            patch("core.config_core.configparser.ConfigParser.read", side_effect=configparser.Error), \
            patch("core.config_core.configparser.ConfigParser") as mock_parser:
        config = Config("test_invalid_config.ini")
        config._load_config()
        mock_parser.assert_called()