import asyncio

from celery import Celery

from comfy.comfy_core import check_queue_task, preview_queue_cleanup
from core.config_core import Config

config_instance = Config()
redis_host = config_instance.get("Redis", "host", default="localhost")
redis_port = config_instance.getint("Redis", "port", default=6379)
task_expiration = config_instance.getint("Celery", "task_expiration", default=600)



celery_app = Celery(
    "tasks",
    broker=f"redis://{redis_host}:{redis_port}/0",
)

celery_app.conf.result_backend = f"redis://{redis_host}:{redis_port}/0"
celery_app.conf.result_expires = task_expiration

celery_app.conf.beat_schedule = {
    "check-queue-every-1-second": {
        "task": "core.celery_core.check_queue_task_celery",
        "schedule": 1.0,
    },
    "expire-old-previews-every-60-seconds": {
        "task": "core.celery_core.preview_queue_cleanup_celery",
        "schedule": 60.0,
    },
}


@celery_app.task
def check_queue_task_celery():
    asyncio.run(check_queue_task())

@celery_app.task
def preview_queue_cleanup_celery():
    asyncio.run(preview_queue_cleanup())
