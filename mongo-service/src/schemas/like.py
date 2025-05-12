from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LikePostDTO(BaseModel):
    user_id: UUID
    content_id: UUID
    created_at: datetime
    model_config = ConfigDict(extra="forbid")


class LikeUpdateDTO(BaseModel):
    id: UUID
    user_id: UUID | None = None
    content_id: UUID | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(extra="forbid")
