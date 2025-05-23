from uuid import UUID, uuid4
from datetime import datetime

from beanie import Document
from pymongo import IndexModel, TEXT
from pydantic import Field


class Entity(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    content_id: UUID
    created_at: datetime


class Like(Entity):
    rate: int = Field(ge=0, le=10)

    class Settings:
        indexes = [IndexModel([("user_id"), ("content_id")], unique=True)]


class Bookmark(Entity):
    class Settings:
        indexes = [IndexModel([("user_id"), ("content_id")], unique=True)]


class Comment(Entity):
    text: str

    class Settings:
        indexes = [IndexModel([("text", TEXT)])]
