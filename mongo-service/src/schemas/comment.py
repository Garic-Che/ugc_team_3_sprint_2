from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict

class CommentPostDTO(BaseModel):
    user_id: UUID
    content_id: UUID
    created_at: datetime
    text: str
    model_config = ConfigDict(extra="forbid")


class CommentUpdateDTO(BaseModel):
    id: UUID
    user_id: UUID | None = None
    content_id: UUID | None = None
    created_at: datetime | None = None
    text: str | None = None
    model_config = ConfigDict(extra="forbid")