import asyncio
import ssl
from datetime import timedelta

from core.config_core import Config
from core.logging_core import setup_logger
from core.metric_core import InfluxDBWriter

logger = setup_logger(__name__)
config_instance = Config()
server_address = config_instance.get("ComfyUI", "server", default="127.0.0.1:8188")
metric = InfluxDBWriter()

# SSL and queue configuration
unsafe_ssl_context = ssl._create_unverified_context()
preview_queue = asyncio.Queue()
expire_old_previews_queue_time: timedelta = timedelta(seconds=60)

# Check server configuration
if not server_address:
    logger.critical("ComfyUI server address not configured.")
    from comfy.exceptions import ComfyUIError
    raise ComfyUIError(
        "ComfyUI server address not configured. Did you forget to pay the server bill again?"
    )
