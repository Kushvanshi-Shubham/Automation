import asyncio

from app.pipeline.celery_app import celery_app


async def _with_fresh_pool(coro):
    """Each Celery task runs in a fresh asyncio.run() loop, but the module-level
    SQLAlchemy engine pools connections bound to the PREVIOUS task's (now dead)
    loop. Abandon the stale pool before touching the DB (close=False: the old
    loop is gone, the connections can't be closed cleanly)."""
    from app.database import engine

    await engine.dispose(close=False)
    return await coro


@celery_app.task(bind=True, name="pipeline.run")
def run_pipeline(self, job_id: str):
    """Celery entrypoint: the pipeline itself is async, so bridge with asyncio.run."""
    from app.pipeline import runner

    return asyncio.run(_with_fresh_pool(runner.run(job_id)))
