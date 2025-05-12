from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class LikeUpdate(BaseModel):
    id: UUID
    user_id: UUID | None = None
    content_id: UUID | None = None
    created_at: datetime | None = None
