import time
import platform
import socket
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from core.env_core import get_env_variable, Envs, load_env_file
# Assuming setup_logger is in utils.logging_core, adjust if necessary
from core.logging_core import setup_logger

# Set up the logger for this module
# The name 'InfluxDBWriter' is used for the logger instance
logger = setup_logger(__name__) 

class InfluxDBWriter:
    """
    Encapsulates the logic for writing data to an InfluxDB instance.

    This class manages the connection to InfluxDB and provides a method 
    for writing data points. Connection settings are loaded from 
    environment variables.
    """
    def __init__(self):
        """
        Initializes the InfluxDBWriter by loading necessary configurations.
        """
        try:
            load_env_file() # Ensure environment variables are loaded
            self.token = get_env_variable(Envs.INFLUXDB_TOKEN)
            self.org = get_env_variable(Envs.INFLUXDB_ORG)
            self.url = get_env_variable(Envs.INFLUXDB_URL)
            self.bucket = get_env_variable(Envs.INFLUXDB_BUCKET)
            
            # Host information is collected once during initialization
            self.host_name = socket.gethostname()
            self.os_name = platform.system()
            logger.info("InfluxDBWriter initialized successfully.")
            
        except Exception as e:
            logger.exception("Failed to initialize InfluxDBWriter.")
            # Depending on the application's needs, you might want to re-raise the exception
            # or handle it in a way that prevents the application from starting without proper config.
            raise e

    def write_data(self, measurement: str, tags: dict, fields: dict):
        """
        Writes a data point to InfluxDB.

        Creates a temporary connection (using 'with') to ensure proper resource 
        closure. Dynamically adds tags and fields to the point. 
        Validates field data types before writing.

        :param measurement: The name of the measurement.
        :type measurement: str
        :param tags: A dictionary of tag key-value pairs.
        :type tags: dict
        :param fields: A dictionary of field key-value pairs.
        :type fields: dict
        :raises ValueError: If a field type is not supported.
        """
        try:
            with InfluxDBClient(url=self.url, token=self.token, org=self.org) as client:
                # Consider making write options configurable if needed
                write_api = client.write_api(write_options=SYNCHRONOUS) 

                point = Point(measurement).tag("host", self.host_name).tag("os", self.os_name)

                # Add tags dynamically
                for tag_key, tag_value in tags.items():
                    point = point.tag(tag_key, str(tag_value)) # Ensure tag value is a string

                # Add fields dynamically and validate types
                for field_key, field_value in fields.items():
                    if isinstance(field_value, (str, int, float, bool)):
                        point = point.field(field_key, field_value)
                    else:
                        # Log a warning instead of raising an immediate error, 
                        # allows processing other fields if desired.
                        # If strict type checking is required, raise ValueError here.
                        logger.warning(f"Unsupported field type for key '{field_key}': {type(field_value)}. Skipping field.")
                        # Or raise ValueError:
                        # raise ValueError(f"Field type for '{field_key}' is not supported: {type(field_value)}")

                # Set timestamp with nanosecond precision
                point = point.time(time.time_ns(), WritePrecision.NS)

                # Write the point to InfluxDB
                write_api.write(bucket=self.bucket, record=point)
                logger.debug(f"Successfully wrote point to measurement '{measurement}' in bucket '{self.bucket}'.")
                
        except ValueError as ve: # Catch specific ValueError from field type check if raised
             logger.error(f"Data validation error while preparing point for InfluxDB: {ve}")
             # Decide if you want to re-raise or just log
             # raise ve 
        except Exception as e:
            # Log any other exceptions during InfluxDB interaction
            logger.exception(f"Error writing data to InfluxDB measurement '{measurement}': {e}")
            # Consider re-raising the exception if the calling code needs to handle it
            # raise e