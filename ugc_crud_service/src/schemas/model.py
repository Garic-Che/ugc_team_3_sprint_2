from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EntityPostDTO(BaseModel):
    user_id: UUID
    content_id: UUID
    created_at: datetime
    model_config = ConfigDict(extra="forbid")


class EntityUpdateDTO(BaseModel):
    id: UUID
    user_id: UUID | None = None
    content_id: UUID | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(extra="forbid")


class CommentPostDTO(EntityPostDTO):
    text: str


class CommentUpdateDTO(EntityUpdateDTO):
    text: str | None = None


class LikePostDTO(EntityPostDTO):
    rate: int = Field(..., ge=0, le=10)


class LikeUpdateDTO(EntityUpdateDTO):
    rate: int | None = Field(None, ge=0, le=10)
