# Kliptos backend — one image, two roles.
# API:    default CMD (migrations + uvicorn)
# Worker: celery -A app.pipeline.celery_app worker -B --loglevel=info
# ffmpeg + fonts are baked in: the render pipeline shells out to ffmpeg and
# burns ASS captions, which need real fonts on the system.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        fonts-dejavu-core \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Rendered files land here before upload to object storage (ephemeral in cloud).
RUN mkdir -p /app/output

EXPOSE 8000

# Render sets $PORT; the default keeps local docker runs working.
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
