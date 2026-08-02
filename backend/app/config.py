import json
from typing import Annotated, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    # Required — the app must refuse to boot without real secrets.
    SECRET_KEY: str
    # Fernet key (base64, 32 bytes) used to encrypt OAuth tokens at rest.
    TOKEN_ENCRYPTION_KEY: str

    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kliptos"
    REDIS_URL: str = "redis://localhost:6379/0"

    OUTPUT_DIR: str = "./output"
    FRONTEND_URL: str = "http://localhost:3000"
    # Backend's own public origin (OAuth redirect target for channel connect).
    API_PUBLIC_URL: str = "http://localhost:8000"

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h; refresh flow lands with frontend session work

    # Ops kill-switch; tests disable it (they hammer endpoints as one user).
    RATE_LIMITS_ENABLED: bool = True

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    YOUTUBE_API_KEY: Optional[str] = None
    PEXELS_API_KEY: Optional[str] = None
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    HIGGSFIELD_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None

    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: Optional[str] = None

    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None

    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    # Public base URL Meta uses to fetch rendered videos (must be internet-reachable;
    # falls back to API_PUBLIC_URL which only works once deployed).
    MEDIA_PUBLIC_URL: Optional[str] = None

    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None

    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # NoDecode: accept plain comma-separated strings, not just JSON lists.
    CORS_ORIGINS: Annotated[List[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        # Accept JSON list ('["http://a"]') or comma-separated string ('http://a,http://b').
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def reject_placeholder_secret(cls, v):
        if v in {"secret", "changeme", "your-secret-key-change-this-in-production"} or len(v) < 32:
            raise ValueError("SECRET_KEY must be a random string of at least 32 characters")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
