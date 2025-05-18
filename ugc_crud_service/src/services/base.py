from uuid import UUID
from typing import TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime

from .models import UpdateModel, CommentUpdateModel, LikeUpdateModel
from models.entity import Entity, Bookmark, Like, Comment


TDocument = TypeVar("TDocument", bound=Entity)
TUpdateModel = TypeVar("TUpdateModel", bound=UpdateModel)


class CUDServiceABC(ABC, Generic[TDocument, TUpdateModel]):
    @abstractmethod
    async def insert(self, entities: list[TDocument]) -> list[TDocument]:
        pass
    
    @abstractmethod
    async def update(self, entity_update: TUpdateModel) -> TDocument:
        pass

    @abstractmethod
    async def delete(self, ids: list[UUID]) -> list[UUID]:
        pass


class ReadServiceABC(ABC, Generic[TDocument]):
    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> list[TDocument]:
        pass

    @abstractmethod
    async def get_by_timerange(self, start: datetime, end: datetime) -> list[TDocument]:
        pass

    @abstractmethod
    async def get_by_content_id(self, content_id: UUID) -> list[TDocument]:
        pass


class BookmarkServiceABC(CUDServiceABC[Bookmark, UpdateModel], ReadServiceABC[Bookmark]):
    pass


class LikeServiceABC(CUDServiceABC[Like, LikeUpdateModel], ReadServiceABC[Like]):
    @abstractmethod
    async def get_avg_content_rate(self, content_id: UUID) -> float:
        pass


class CommentServiceABC(CUDServiceABC[Comment, CommentUpdateModel], ReadServiceABC[Comment]):
    @abstractmethod
    async def search_by_text(self, term: str) -> list[Comment]:
        pass
