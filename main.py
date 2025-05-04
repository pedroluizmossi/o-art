import subprocess  # nosec B404
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from api.auth_api import router as auth_router
from api.image_api import router as image_router
from api.model_api import router as model_router
from api.plan_api import router as plan_router
from api.scalar_docs_api import router as scalar_docs_router
from api.user_folder_api import router as user_folder_router
from api.user_image_api import router as user_image_router
from api.webhook_api import router as webhook_router
from api.websocket_api import router as websocket_router
from api.workflow_api import router as workflow_router
from core.config_core import Config
from core.db_core import create_db
from core.logging_core import cleanup_old_logs, setup_logger
from core.minio_core import create_default_bucket
from handler.start_data_handler import initial_data
from resources.openapi_tags_metadata import tags_metadata

load_dotenv()
logger = setup_logger(__name__)
config = Config()
worker_process = None
beat_process = None

def _cleanup_logs():
    log_directory = config.get("Logs", "path", "./logs")
    max_log_files = config.getint("Logs", "max_files", 10)
    if log_directory and max_log_files >= 0:
        cleanup_old_logs(log_dir=log_directory, max_files=max_log_files)
    else:
        logger.warning("Log cleanup skipped: Invalid directory or max_files configuration.")

def _start_subprocesses():
    worker_cmd = [
        sys.executable, "-m", "celery", "-A", "core.celery_core.celery_app",
        "worker", "--loglevel=warning", "--pool=solo"
    ]
    beat_cmd = [
        sys.executable, "-m", "celery", "-A", "core.celery_core.celery_app",
        "beat", "--loglevel=warning"
    ]
    worker_proc = subprocess.Popen(worker_cmd)  # nosec B603
    logger.info("Worker process started with PID: %s", worker_proc.pid)
    beat_proc = subprocess.Popen(beat_cmd)  # nosec B603
    logger.info("Beat process started with PID: %s", beat_proc.pid)
    return worker_proc, beat_proc

def _stop_subprocess(proc, desc):
    if proc:
        logger.info("Stopping %s process...", desc)
        proc.terminate()
        try:
            proc.wait(timeout=10)
            logger.info("%s process stopped gracefully.", desc)
        except subprocess.TimeoutExpired:
            logger.warning(
                "%s process did not stop in time, forcing shutdown (SIGKILL)...", desc
            )
            proc.kill()
            proc.wait()
            logger.info("%s process kill forced.", desc)

def _setup_minio_bucket():
    try:
        create_default_bucket()
    except Exception as e:
        logger.error("Failed to create default MinIO bucket: %s", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db()
    await initial_data()
    global worker_process, beat_process
    logger.info("Starting worker and beat processes...")
    try:
        _cleanup_logs()
    except Exception as e:
        logger.error("Failed to run initial log cleanup: %s", e, exc_info=True)
    try:
        worker_process, beat_process = _start_subprocesses()
    except Exception as e:
        logger.error("Failed to start worker/beat: %s", e)
    _setup_minio_bucket()
    yield
    _stop_subprocess(worker_process, "worker")
    _stop_subprocess(beat_process, "beat")

app = FastAPI(lifespan=lifespan, openapi_tags=tags_metadata)
app.include_router(auth_router)
app.include_router(user_folder_router)
app.include_router(user_image_router)
app.include_router(webhook_router)
app.include_router(image_router)
app.include_router(workflow_router)
app.include_router(model_router)
app.include_router(plan_router)
app.include_router(websocket_router)
app.include_router(scalar_docs_router)