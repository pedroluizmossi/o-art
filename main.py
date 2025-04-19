import time
from contextlib import asynccontextmanager
import subprocess
import sys

from fastapi import FastAPI, Response, HTTPException
from core.env_core import load_env_file
from core.config_core import Config
from core.db_core import create_db

###Routes
from api.auth_api import router as auth_router
from api.webhook_api import router as webhook_router
from api.image_api import router as image_router
from api.websocket_api import router as websocket_router

from core.logging_core import setup_logger
logger = setup_logger(__name__)

load_env_file()
create_db()

worker_process = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_process, beat_process
    logger.info("Iniciando os processos worker e beat...")

    try:
        worker_command = [
            sys.executable, "-m", "celery", "-A", "core.celery_core.celery_app", "worker", "--loglevel=warning",
            "--pool=solo"
        ]
        worker_process = subprocess.Popen(worker_command)
        logger.info(f"Processo worker iniciado com PID: {worker_process.pid}")

        beat_command = [
            sys.executable, "-m", "celery", "-A", "core.celery_core.celery_app", "beat", "--loglevel=warning"
        ]
        beat_process = subprocess.Popen(beat_command)
        logger.info(f"Processo beat iniciado com PID: {beat_process.pid}")

    except Exception as e:
        logger.error(f"Falha ao iniciar worker/beat: {e}")

    yield

    # Finalizando ambos:
    for proc, desc in [(worker_process, "worker"), (beat_process, "beat")]:
        if proc:
            logger.info(f"Parando o processo {desc}...")
            proc.terminate()
            try:
                proc.wait(timeout=10)
                logger.info(f"Processo {desc} terminado graciosamente.")
            except subprocess.TimeoutExpired:
                logger.warning(f"Processo {desc} não terminou a tempo, forçando parada (SIGKILL)...")
                proc.kill()
                proc.wait()
                logger.info(f"Processo {desc} forçado a parar.")


app = FastAPI(lifespan=lifespan)
# --- Fim da modificação ---

app.include_router(auth_router)
app.include_router(webhook_router)
app.include_router(image_router)
app.include_router(websocket_router)
config = Config()
