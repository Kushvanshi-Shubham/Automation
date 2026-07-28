from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChannelResponse(BaseModel):
    id: UUID
    youtube_channel_id: Optional[str]
    channel_name: Optional[str]
    is_active: Optional[bool]
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class ConnectUrlResponse(BaseModel):
    auth_url: str
