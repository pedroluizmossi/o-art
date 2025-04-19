from celery import Celery
from core.config_core import Config
import asyncio
from comfy.comfy_core import check_queue_task
from celery.schedules import crontab

config = Config()
redis_cfg = Config.Redis(config)
redis_host = redis_cfg.get_host()
redis_port = redis_cfg.get_port()

celery_app = Celery(
    'tasks',
    broker=f'redis://{redis_host}:{redis_port}/0',
    )

celery_app.conf.result_backend = f'redis://{redis_host}:{redis_port}/0'

celery_app.conf.beat_schedule = {
    'check-queue-every-1-second': {
        'task': 'core.celery_core.check_queue_task_celery',
        'schedule': 1.0,
    },
}

@celery_app.task
def check_queue_task_celery():
    asyncio.run(check_queue_task())
