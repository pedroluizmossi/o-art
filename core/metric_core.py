import time
import platform
import socket
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from core.env_core import get_env_variable, Envs

from core.logging_core import setup_logger

logger = setup_logger(__name__)


class InfluxDBWriter:
    def __init__(self):
        try:
            self.token = get_env_variable(Envs.INFLUXDB_TOKEN)
            self.org = get_env_variable(Envs.INFLUXDB_ORG)
            self.url = get_env_variable(Envs.INFLUXDB_URL)
            self.bucket = get_env_variable(Envs.INFLUXDB_BUCKET)

            if not all([self.token, self.org, self.url, self.bucket]):
                logger.error(
                    "Missing one or more InfluxDB environment variables (TOKEN, ORG, URL, BUCKET). Metrics will be disabled.")
                self.enabled = False
            else:
                self.enabled = True

            self.host_name = socket.gethostname()
            self.os_name = platform.system()
            if self.enabled:
                logger.info("InfluxDBWriter initialized successfully.")
            else:
                logger.warning("InfluxDBWriter initialized but is disabled due to missing configuration.")

        except Exception as e:
            logger.exception("Failed to initialize InfluxDBWriter.")
            self.enabled = False

    def write_data(self, measurement: str, tags: dict, fields: dict):
        if not self.enabled:
            logger.debug("InfluxDB is disabled, skipping metric writing.")
            return
        """
        Write data to InfluxDB.
        Args:
            measurement (str): The measurement name in InfluxDB.
            tags (dict): A dictionary of tags to add to the point.
            fields (dict): A dictionary of fields to add to the point.
        """
        try:
            with InfluxDBClient(url=self.url, token=self.token, org=self.org) as client:
                # Consider making write options configurable if needed
                write_api = client.write_api(write_options=SYNCHRONOUS)

                point = Point(measurement).tag("host", self.host_name).tag("os", self.os_name)

                # Add tags dynamically
                for tag_key, tag_value in tags.items():
                    point = point.tag(tag_key, str(tag_value))  # Ensure tag value is a string

                # Add fields dynamically and validate types
                for field_key, field_value in fields.items():
                    if isinstance(field_value, (str, int, float, bool)):
                        point = point.field(field_key, field_value)
                    else:
                        # Log a warning instead of raising an immediate error, 
                        # allows processing other fields if desired.
                        # If strict type checking is required, raise ValueError here.
                        logger.warning(
                            f"Unsupported field type for key '{field_key}': {type(field_value)}. Skipping field.")
                        # Or raise ValueError:
                        # raise ValueError(f"Field type for '{field_key}' is not supported: {type(field_value)}")

                # Set timestamp with nanosecond precision
                point = point.time(time.time_ns(), WritePrecision.NS)

                # Write the point to InfluxDB
                write_api.write(bucket=self.bucket, record=point)
                logger.debug(f"Successfully wrote point to measurement '{measurement}' in bucket '{self.bucket}'.")

        except ValueError as ve:  # Catch specific ValueError from field type check if raised
            logger.error(f"Data validation error while preparing point for InfluxDB: {ve}")
            # Decide if you want to re-raise or just log
            # raise ve
        except Exception as e:
            # Log any other exceptions during InfluxDB interaction
            logger.exception(f"Error writing data to InfluxDB measurement '{measurement}': {e}")
            # Consider re-raising the exception if the calling code needs to handle it
            # raise e
