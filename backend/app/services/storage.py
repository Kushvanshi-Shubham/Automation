"""Object storage for media files (S3-compatible; Cloudflare R2 in prod).

Local dev needs none of this: when the S3 settings are absent, files stay
on the local disk under OUTPUT_DIR and are served by the /media mount.
In the cloud, the API and the render worker are DIFFERENT machines with
ephemeral disks — every file that crosses a process boundary (uploads,
finished renders, image slides) must live in the bucket.

Keys are stable and readable:
    uploads/{user_id}/{asset_id}{ext}     creator footage
    renders/{video_id}/final.mp4          finished shorts
    renders/{video_id}/img_00.jpg         image-post slides
"""
import logging
from functools import lru_cache
from pathlib import Path

from app.config import settings

logger = logging.getLogger("kliptos.storage")

_CONTENT_TYPES = {
    ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
    ".mkv": "video/x-matroska", ".mp3": "audio/mpeg", ".m4a": "audio/mp4",
    ".wav": "audio/wav", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def enabled() -> bool:
    return bool(
        settings.S3_BUCKET_NAME
        and settings.S3_ENDPOINT_URL
        and settings.AWS_ACCESS_KEY_ID
        and settings.AWS_SECRET_ACCESS_KEY
    )


@lru_cache(maxsize=1)
def _client():
    import boto3
    from botocore.config import Config as BotoConfig

    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        region_name=settings.S3_REGION or "auto",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=BotoConfig(retries={"max_attempts": 3, "mode": "standard"}),
    )


def public_url(key: str) -> str:
    """The URL browsers fetch this object from."""
    base = (settings.S3_PUBLIC_URL or "").rstrip("/")
    return f"{base}/{key}"


def upload(local_path: Path, key: str) -> str:
    """Upload a file; returns its public URL. Blocking — call off the loop
    in async contexts (the render worker calls it from sync code)."""
    content_type = _CONTENT_TYPES.get(local_path.suffix.lower(), "application/octet-stream")
    _client().upload_file(
        str(local_path), settings.S3_BUCKET_NAME, key,
        ExtraArgs={"ContentType": content_type},
    )
    logger.info("uploaded %s -> %s", local_path.name, key)
    return public_url(key)


def download(key: str, dest: Path) -> Path:
    """Fetch an object to a local path (worker pulls sources before ffmpeg)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    _client().download_file(settings.S3_BUCKET_NAME, key, str(dest))
    return dest


def delete(key: str) -> None:
    """Best-effort delete — a missing object must never fail user flows."""
    try:
        _client().delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    except Exception as exc:
        logger.warning("storage delete failed for %s: %s", key, exc)


def resolve_source(path_or_key: str, workdir: Path) -> Path:
    """A local Path for an asset, wherever it lives.

    Asset.path holds a local filesystem path in dev and a bucket key in
    prod (keys never have a drive letter or leading slash/dot). Downloads
    land in the caller's workdir so render cleanup removes them.
    """
    p = Path(path_or_key)
    if p.exists():
        return p.resolve()
    if enabled() and not path_or_key.startswith((".", "/", "\\")) and ":" not in path_or_key:
        return download(path_or_key, workdir / Path(path_or_key).name)
    raise RuntimeError("source file is missing — re-upload it")
