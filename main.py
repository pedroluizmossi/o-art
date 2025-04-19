from contextlib import asynccontextmanager
import subprocess
import sys

from fastapi import FastAPI, Response, HTTPException
from core.config_core import Config
from core.db_core import create_db

###Routes
from api.auth_api import router as auth_router
from api.webhook_api import router as webhook_router
from api.image_api import router as image_router
from api.websocket_api import router as websocket_router

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from core.logging_core import setup_logger, cleanup_old_logs

logger = setup_logger(__name__)

config = Config()

create_db()

worker_process = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_process, beat_process
    logger.info("Iniciando os processos worker e beat...")

    try:
        from core.config_core import Config

        config_instance = Config()
        log_directory = config_instance.get("Logs", "path", "./logs")
        max_log_files = config_instance.getint("Logs", "max_files", 10)
        if log_directory and max_log_files >= 0:
            cleanup_old_logs(log_dir=log_directory, max_files=max_log_files)
        else:
            logger.warning(
                "Log cleanup skipped: Invalid directory or max_files configuration."
            )
    except Exception as e:
        logger.error("Failed to run initial log cleanup: %s", e, exc_info=True)

    try:
        worker_command = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "core.celery_core.celery_app",
            "worker",
            "--loglevel=warning",
            "--pool=solo",
        ]
        worker_process = subprocess.Popen(worker_command)
        logger.info("Processo worker iniciado com PID: %s", worker_process.pid)

        beat_command = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "core.celery_core.celery_app",
            "beat",
            "--loglevel=warning",
        ]
        beat_process = subprocess.Popen(beat_command)
        logger.info("Processo beat iniciado com PID: %s", beat_process.pid)

    except Exception as e:
        logger.error("Falha ao iniciar worker/beat: %s", e)

    yield

    for proc, desc in [(worker_process, "worker"), (beat_process, "beat")]:
        if proc:
            logger.info("Parando o processo %s...", desc)
            proc.terminate()
            try:
                proc.wait(timeout=10)
                logger.info("Processo %s terminado graciosamente.", desc)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Processo %s não terminou a tempo, forçando parada (SIGKILL)...",
                    desc,
                )
                proc.kill()
                proc.wait()
                logger.info("Processo %s forçado a parar.", desc)


app = FastAPI(lifespan=lifespan)
# --- Fim da modificação ---

app.include_router(auth_router)
app.include_router(webhook_router)
app.include_router(image_router)
app.include_router(websocket_router)
