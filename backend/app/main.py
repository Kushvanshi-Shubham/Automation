import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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
from app.websocket.progress import manager

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


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.websocket("/ws/pipeline/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    # NOTE: progress events will flow via Redis pub/sub once the pipeline lands;
    # this endpoint only manages subscriber connections.
    await manager.connect(websocket, job_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
