from uuid import UUID, uuid4
from datetime import datetime

import pymongo
from beanie import Document
from pymongo import IndexModel
from pydantic import Field


class Entity(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    created_at: datetime


class Like(Entity):
    content_id: UUID

    class Settings:
        indexes = [
            IndexModel([("user_id", pymongo.ASCENDING), ("content_id", pymongo.ASCENDING)], unique=True)
        ]


class Bookmark(Entity):
    content_id: UUID

    class Settings:
        indexes = [
            IndexModel([("user_id", pymongo.ASCENDING), ("content_id", pymongo.ASCENDING)], unique=True)
        ]