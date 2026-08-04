from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

# Neon/Supabase pooled connections (pgbouncer/supavisor in transaction mode)
# break asyncpg's prepared-statement cache — disable it when the URL points
# at a pooler. Direct connections keep the cache (local dev, Render PG).
_connect_args = {}
if "-pooler" in settings.DATABASE_URL or "pgbouncer" in settings.DATABASE_URL:
    _connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # cloud DBs drop idle connections; recycle dead ones
    connect_args=_connect_args,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
