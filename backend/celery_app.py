from celery import Celery
from config import REDIS_URL

celery = Celery(
    "patchpilot",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.celery_tasks"]
)
celery.conf.task_track_started = True
