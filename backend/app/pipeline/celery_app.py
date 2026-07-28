from celery import Celery

from app.config import settings

celery_app = Celery(
    "kliptos_pipeline",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.pipeline.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
