from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

from app.routers import (
    auth, topics, scripts, pipeline, videos, uploads, analytics, billing
)
from app.websocket.progress import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Kliptos API",
    description="AI-powered YouTube Shorts automation SaaS platform",
    version="1.0.0",
    lifespan=lifespan
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
    return {"status": "ok"}

@app.websocket("/ws/pipeline/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Placeholder for handling incoming WS messages
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
