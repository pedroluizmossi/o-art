import influxdb_client, os, time
import platform
import socket
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from utils.env_core import get_env_variable, Envs, load_env_file

load_env_file()

token = get_env_variable(Envs.INFLUXDB_TOKEN)
org = get_env_variable(Envs.INFLUXDB_ORG)
url = get_env_variable(Envs.INFLUXDB_URL)
bucket = get_env_variable(Envs.INFLUXDB_BUCKET)

host_name = socket.gethostname()
os_name = platform.system()



def write_data(measurement, tags, fields):
    """
    Writes data to an InfluxDB instance using the specified parameters.

    This function sends a measurement point to the InfluxDB database. The measurement
    can include dynamic tags and fields, which are used to describe metadata and data
    points, respectively. Each tag and field is added dynamically to the measurement.
    The timestamp is automatically set with nanosecond precision. The InfluxDB client
    operates with a synchronous write interface. The function ensures that field values
    are of supported types before writing, raising an error in case of unsupported types.

    :param measurement: The name of the measurement to be written to the database.
    :type measurement: str
    :param tags: A dictionary of tag keys and values to annotate the measurement point.
    :type tags: dict
    :param fields: A dictionary of field keys and values representing the data points of
        the measurement.
    :type fields: dict
    :return: None
    """
    with InfluxDBClient(url=url, token=token, org=org) as write_client:
        write_api = write_client.write_api(
            write_options=SYNCHRONOUS, # Synchronous write
            batch_size=5000, # 5 seconds
            flush_interval=10_000, # 10 seconds
            jitter_interval=2_000, # 2 seconds
            retry_interval=5_000, # 5 seconds
            max_retries=5, # 5 retries
            timeout=10_000, # 10 seconds
        )

        point = Point(measurement).tag("host", host_name).tag("os", os_name)

        # Adicionar cada tag de forma dinâmica
        for tag_key, tag_value in tags.items():
            point = point.tag(tag_key, str(tag_value))

        # Adicionar cada campo de forma dinâmica
        for field_key, field_value in fields.items():
            # Certifique-se de que o valor seja um tipo suportado pelo InfluxDB
            if isinstance(field_value, (str, int, float, bool)):
                point = point.field(field_key, field_value)
            else:
                raise ValueError(f"Type of field '{field_key}' is not supported: {type(field_value)}")

        # Configurar o timestamp no ponto
        point = point.time(time.time_ns(), WritePrecision.NS)

        # Escrever o ponto no InfluxDB
        write_api.write(bucket=bucket, record=point)

