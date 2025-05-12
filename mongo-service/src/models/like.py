from uuid import UUID, uuid4
from datetime import datetime

import pymongo
from beanie import Document
from pymongo import IndexModel
from pydantic import Field


class Like(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    content_id: UUID
    created_at: datetime

    class Settings:
        indexes = [
            IndexModel([("user_id", pymongo.ASCENDING), ("content_id", pymongo.ASCENDING)], unique=True)
        ]