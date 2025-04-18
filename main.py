from fastapi import FastAPI, Response, HTTPException
from comfy.comfy_core import generate_image, get_queue
from core.env_core import load_env_file
from core.metric_core import InfluxDBWriter
from core.config_core import Config
from core.db_core import create_db

###Routes
from api.auth_api import router as auth_router
from api.webhook_api import router as webhook_router

load_env_file()
# Initialize the database
create_db()
app = FastAPI()
app.include_router(auth_router)
app.include_router(webhook_router)

config = Config()

