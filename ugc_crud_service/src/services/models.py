from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class UpdateModel(BaseModel):
    id: UUID
    user_id: UUID | None = None
    content_id: UUID | None = None
    created_at: datetime | None = None


class CommentUpdateModel(UpdateModel):
    text: str | None = None