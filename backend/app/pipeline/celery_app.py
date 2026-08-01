from celery import Celery

from app.config import settings

celery_app = Celery(
    "kliptos_pipeline",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.pipeline.tasks",
        "app.pipeline.upload_tasks",
        "app.pipeline.ig_upload_tasks",
        "app.pipeline.series_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "series-autopilot-tick": {"task": "series.tick", "schedule": 900.0},  # every 15 min
    },
)
