from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, HTTPException
from core.env_core import load_env_file
from core.config_core import Config
from core.db_core import create_db
from comfy.comfy_core import check_queue
import threading
import asyncio

###Routes
from api.auth_api import router as auth_router
from api.webhook_api import router as webhook_router
from api.image_api import router as image_router
from api.websocket_api import router as websocket_router

from core.logging_core import setup_logger
logger = setup_logger(__name__)

load_env_file()
# Initialize the database
create_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Event handler for application startup.
    """
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(webhook_router)
app.include_router(image_router)
app.include_router(websocket_router)
config = Config()




