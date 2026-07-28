import time

from app.pipeline.celery_app import celery_app
from app.services.progress import publish_progress


@celery_app.task(bind=True)
def run_pipeline(self, job_id: str, video_id: str, visual_engine: str):
    """Placeholder pipeline: real stages land in the S1 pipeline milestone.

    Progress events already flow through the production path
    (Redis pub/sub -> API WebSocket -> browser).
    """
    publish_progress(job_id, status="running", stage="starting", percent=0)
    time.sleep(1)
    publish_progress(job_id, status="running", stage="audio", percent=30)
    time.sleep(1)
    publish_progress(job_id, status="running", stage="visuals", percent=70)
    time.sleep(1)
    publish_progress(job_id, status="completed", stage="completed", percent=100)
    return {"job_id": job_id, "video_id": video_id, "status": "completed"}
