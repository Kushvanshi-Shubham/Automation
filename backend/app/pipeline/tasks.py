import asyncio

from app.pipeline.celery_app import celery_app


@celery_app.task(bind=True, name="pipeline.run")
def run_pipeline(self, job_id: str):
    """Celery entrypoint: the pipeline itself is async, so bridge with asyncio.run."""
    from app.pipeline import runner

    return asyncio.run(runner.run(job_id))
