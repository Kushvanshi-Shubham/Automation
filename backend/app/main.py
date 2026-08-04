import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import (
    analytics,
    api_keys,
    auth,
    billing,
    channels,
    feedback,
    instagram,
    media,
    pipeline,
    scripts,
    series,
    styles,
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


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response

app.include_router(auth.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(scripts.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(channels.router, prefix="/api")
app.include_router(api_keys.router, prefix="/api")
app.include_router(instagram.router, prefix="/api")
app.include_router(series.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(styles.router, prefix="/api")


# Rendered videos (local dev storage; object storage replaces this in prod).
_media_dir = Path(settings.OUTPUT_DIR)
_media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media_dir)), name="media")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.websocket("/ws/pipeline/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str, token: str = ""):
    """Forward Redis pub/sub progress events for this job to the browser.

    Requires ?token=<jwt> and verifies the job belongs to that user —
    job UUIDs alone must not grant access to progress streams.
    """
    from uuid import UUID as _UUID

    from app.core.security import decode_access_token
    from app.database import AsyncSessionLocal
    from app.models.pipeline_job import PipelineJob

    subject = decode_access_token(token) if token else None
    if subject is None:
        await websocket.close(code=4401)
        return
    try:
        job_uuid = _UUID(job_id)
        user_uuid = _UUID(subject)
    except ValueError:
        await websocket.close(code=4403)
        return
    async with AsyncSessionLocal() as db:
        job = await db.get(PipelineJob, job_uuid)
    if job is None or job.user_id != user_uuid:
        await websocket.close(code=4403)
        return

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
