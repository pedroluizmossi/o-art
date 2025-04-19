from celery import Celery
from core.config_core import Config
import asyncio
from comfy.comfy_core import check_queue_task

config_instance = Config()
redis_host = config_instance.get("Redis", "host", default="localhost")
redis_port = config_instance.getint("Redis", "port", default=6379)

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
