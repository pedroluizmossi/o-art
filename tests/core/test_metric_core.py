import os
from unittest.mock import patch

import pytest

from core.env_core import Envs
from core.metric_core import InfluxDBWriter


def test_influxdbwriter_initialization_with_valid_env_vars():
    with patch.dict(os.environ, {
        Envs.INFLUXDB_TOKEN: "test_token",
        Envs.INFLUXDB_ORG: "test_org",
        Envs.INFLUXDB_URL: "http://localhost:8086",
        Envs.INFLUXDB_BUCKET: "test_bucket"
    }):
        writer = InfluxDBWriter()
        assert writer.enabled is True
        assert writer.token == "test_token"
        assert writer.org == "test_org"
        assert writer.url == "http://localhost:8086"
        assert writer.bucket == "test_bucket"


def test_influxdbwriter_initialization_with_missing_env_vars():
    with patch.dict(os.environ, {
        Envs.INFLUXDB_TOKEN: "test_token",
        Envs.INFLUXDB_ORG: "",
        Envs.INFLUXDB_URL: "http://localhost:8086",
        Envs.INFLUXDB_BUCKET: "test_bucket"
    }):
        writer = InfluxDBWriter()
        assert writer.enabled is False


def test_influxdbwriter_write_data_disabled():
    with patch.dict(os.environ, {
        Envs.INFLUXDB_TOKEN: "",
        Envs.INFLUXDB_ORG: "",
        Envs.INFLUXDB_URL: "",
        Envs.INFLUXDB_BUCKET: ""
    }):
        writer = InfluxDBWriter()
        with patch("core.metric_core.logger.debug") as mock_logger:
            writer.write_data(
                measurement="test_measurement",
                tags={},
                fields={}
            )
            mock_logger.assert_called_with("InfluxDB is disabled, skipping metric writing.")

@pytest.fixture
def influxdb_writer():
    with patch('core.metric_core.InfluxDBClient'):
        writer = InfluxDBWriter()
        writer.enabled = True
        writer.url = "http://example.com"
        writer.token = "test-token"
        writer.org = "test-org"
        writer.bucket = "test-bucket"
        writer.host_name = "test-host"
        writer.os_name = "test-os"
        yield writer


def test_write_data_disabled(influxdb_writer):
    influxdb_writer.enabled = False
    with patch('core.metric_core.logger') as mock_logger:
        influxdb_writer.write_data("test_measurement", {}, {})

        mock_logger.debug.assert_called_with("InfluxDB is disabled, skipping metric writing.")


def test_write_data_invalid_field_type(influxdb_writer):
    with patch('core.metric_core.logger') as mock_logger:
        measurement = "test_measurement"
        tags = {"tag1": "value1"}
        fields = {"field1": {}}

        influxdb_writer.write_data(measurement, tags, fields)
        mock_logger.warning.assert_called_with(
            "Unsupported field type for key 'field1': <class 'dict'>. Skipping field."
        )