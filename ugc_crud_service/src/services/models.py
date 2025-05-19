from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class UpdateModel(BaseModel):
    id: UUID
    user_id: UUID | None = None
    content_id: UUID | None = None
    created_at: datetime | None = None


class CommentUpdateModel(UpdateModel):
    text: str | None = None


class LikeUpdateModel(UpdateModel):
    rate: int | None = Field(None, ge=0, le=10)