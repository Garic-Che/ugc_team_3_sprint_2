from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class UpdateModel(BaseModel):
    id: UUID


class LikeUpdate(UpdateModel):
    user_id: UUID | None = None
    content_id: UUID | None = None
    created_at: datetime | None = None


class BookmarkUpdate(UpdateModel):
    user_id: UUID | None = None
    content_id: UUID | None = None
    created_at: datetime | None = None