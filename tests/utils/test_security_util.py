from unittest.mock import Mock, patch
from urllib.request import Request

import pytest

from utils.security_util import safe_urlopen


def test_safe_urlopen_valid_http_url():
    url = "http://example.com"
    with patch("utils.security_util.urlopen", return_value=Mock()) as mock_urlopen:
        result = safe_urlopen(url)
        assert result == mock_urlopen.return_value
        mock_urlopen.assert_called_once_with(url)


def test_safe_urlopen_valid_https_url():
    url = "https://example.com"
    with patch("utils.security_util.urlopen", return_value=Mock()) as mock_urlopen:
        result = safe_urlopen(url)
        assert result == mock_urlopen.return_value
        mock_urlopen.assert_called_once_with(url)


def test_safe_urlopen_invalid_scheme():
    url = "ftp://example.com"
    with pytest.raises(ValueError, match="Invalid URL scheme: ftp."):
        safe_urlopen(url)


def test_safe_urlopen_request_object():
    request = Request("http://example.com")
    with patch("utils.security_util.urlopen", return_value=Mock()) as mock_urlopen:
        result = safe_urlopen(request)
        assert result == mock_urlopen.return_value
        mock_urlopen.assert_called_once_with(request)


def test_safe_urlopen_invalid_type():
    with pytest.raises(TypeError, match="URL deve ser string ou urllib.request.Request"):
        safe_urlopen(123)
