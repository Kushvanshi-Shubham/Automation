import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import (
    analytics,
    auth,
    billing,
    pipeline,
    scripts,
    topics,
    uploads,
    videos,
)
from app.services import progress as progress_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("kliptos")

app = FastAPI(
    title="Kliptos API",
    description="AI-powered YouTube Shorts automation SaaS platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(scripts.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(billing.router, prefix="/api")


# Rendered videos (local dev storage; object storage replaces this in prod).
_media_dir = Path(settings.OUTPUT_DIR)
_media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media_dir)), name="media")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.websocket("/ws/pipeline/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """Forward Redis pub/sub progress events for this job to the browser.

    Celery workers publish via app.services.progress.publish_progress; this
    endpoint is a pure subscriber, so it works across processes/containers.
    """
    await websocket.accept()
    client = progress_service.async_redis()
    pubsub = client.pubsub()
    await pubsub.subscribe(progress_service.channel_for(job_id))
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    except Exception:  # client went away mid-send or Redis dropped
        logger.exception("websocket forwarding stopped for job %s", job_id)
    finally:
        await pubsub.unsubscribe()
        await pubsub.aclose()
        await client.aclose()
