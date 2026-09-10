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
        "app.pipeline.asset_tasks",
        "app.pipeline.style_tasks",
        "app.pipeline.reaper",
        "app.pipeline.proof",
        "app.pipeline.credit_grants",
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
        # Refund and clear renders no worker ever finished (see reaper.py).
        "reap-stale-renders": {"task": "pipeline.reap_stale", "schedule": 600.0},  # every 10 min
        # Monthly allowances renew on a per-user clock, so this only has to
        # run often enough to catch each user's anniversary — daily is
        # plenty, and cheap because the query only returns users who are due.
        "grant-monthly-credits": {"task": "billing.grant_monthly_credits", "schedule": 86400.0},
    },
)
