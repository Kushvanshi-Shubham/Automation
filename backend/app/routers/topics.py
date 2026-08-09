from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import rate_limit
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicListResponse
from app.services.harvester import harvest_topics
from app.services.niches import NICHES, VALID_CATEGORIES

router = APIRouter(prefix="/topics", tags=["Topics"], dependencies=[Depends(get_current_user)])


@router.get("/niches")
async def list_niches():
    """Available niche filters (server-driven so UI stays in sync)."""
    return {"items": [{"key": k, "label": v["label"]} for k, v in NICHES.items()]}


@router.get("", response_model=TopicListResponse)
async def get_topics(category: str | None = None, db: AsyncSession = Depends(get_db)):
    from app.schemas.topic import TopicResponse
    from app.services.formats import LEGACY_FORMAT_MAP

    query = select(Topic).order_by(Topic.score.desc()).limit(60)
    if category:
        if category not in VALID_CATEGORIES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown category")
        query = query.where(Topic.category == category)
    result = await db.execute(query)
    items = []
    for t in result.scalars().all():
        row = TopicResponse.model_validate(t)
        # Rows harvested before the format pack stored engine names.
        if row.best_format in LEGACY_FORMAT_MAP:
            row.best_format = LEGACY_FORMAT_MAP[row.best_format]
        items.append(row)
    return {"items": items}


# Where trends are harvested from. India first — this product is India-first
# and the old hardcoded "US" meant an Indian creator saw American trends.
REGIONS = {
    "IN": "India",
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "SG": "Singapore",
    "AE": "United Arab Emirates",
}
DEFAULT_REGION = "IN"


@router.get("/regions")
async def list_regions():
    return {"items": [{"key": k, "label": v} for k, v in REGIONS.items()], "default": DEFAULT_REGION}


@router.post("/refresh", dependencies=[Depends(rate_limit("topics_refresh"))])
async def refresh_topics(
    geo: str = DEFAULT_REGION,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Harvest fresh topics for a region.

    Returns per-source errors so the UI can say WHICH source went quiet
    instead of silently showing half the trends (Google Trends throttles
    datacenter IPs — the API is in a datacenter, so this happens).
    """
    geo = (geo or DEFAULT_REGION).upper()
    if geo not in REGIONS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unsupported region")
    result = await harvest_topics(db, geo=geo)
    result["geo"] = geo
    return result


@router.post("/custom")
async def custom_topic(prompt: str):
    # Lands with the script-studio milestone (LLM-expanded custom topics).
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Custom topics not yet available")
