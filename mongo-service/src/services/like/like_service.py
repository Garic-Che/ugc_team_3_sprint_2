from uuid import UUID
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Iterable

from beanie import UpdateResponse
from beanie.operators import In
from pymongo.errors import BulkWriteError, DuplicateKeyError

from models.like import Like
from .models import LikeUpdate
from exceptions.services import DuplicateError, NotFoundKeyError


class LikeServiceABC(ABC):
    @abstractmethod
    async def insert(self, likes: list[Like]) -> list[UUID]:
        pass

    @abstractmethod
    async def get_user_likes(self, user_id: UUID) -> list[Like]:
        pass

    @abstractmethod
    async def get_content_likes(self, content_id: UUID) -> list[Like]:
        pass

    @abstractmethod
    async def get_timerange_likes(self, start: datetime, end: datetime) -> list[Like]:
        pass

    @abstractmethod
    async def delete(self, ids: list[UUID]):
        pass

    @abstractmethod
    async def update(self, like: LikeUpdate):
        pass


class LikeService(LikeServiceABC):
    async def insert(self, likes: list[Like]) -> list[UUID]:
        try:
            await Like.insert_many(likes)
            return likes
        except BulkWriteError as bwe:
            write_errors = bwe.details.get("writeErrors", [])
            for error in write_errors:
                if error.get("code") == 11000:
                    raise DuplicateError("like")
            raise bwe

    async def get_user_likes(self, user_id: UUID) -> list[Like]:
        user_likes = await Like.find(Like.user_id == user_id).to_list()
        if not user_likes:
            return []
        return user_likes
    
    async def get_content_likes(self, content_id: UUID) -> list[Like]:
        content_likes = await Like.find(Like.content_id == content_id).to_list()
        if not content_likes:
            return []
        return content_likes
    
    async def get_timerange_likes(self, start: datetime, end: datetime) -> list[Like]:
        timerange_likes = await Like.find(Like.created_at >= start, Like.created_at < end).to_list()
        if not timerange_likes:
            return []
        return timerange_likes
    
    async def delete(self, ids: list[UUID]):
        nonexistent_ids = await self._get_nonexistent_ids(ids)
        if nonexistent_ids:
            raise NotFoundKeyError(nonexistent_ids)
        await Like.find_many(In(Like.id, ids)).delete_many()
        return ids

    async def _get_nonexistent_ids(self, ids: list[UUID]) -> Iterable[UUID]:
        existing_likes = await Like.find_many(In(Like.id, ids)).to_list()
        if len(existing_likes) == len(ids):
            return []
        existing_ids = [like.id for like in existing_likes]
        nonexistent_ids = set(ids).difference(existing_ids)
        return nonexistent_ids

    async def update(self, like_update: LikeUpdate):
        try:
            document = await Like.get(like_update.id)
            if not document:
                raise NotFoundKeyError([like_update.id])
            update_mapping = like_update.model_dump(exclude_unset=True)
            updated_document = (await Like.find_one(Like.id == like_update.id)
                                .update_one({"$set": update_mapping}, response_type=UpdateResponse.NEW_DOCUMENT))
            return updated_document
        except DuplicateKeyError:
            raise DuplicateError("like")


def get_like_service() -> LikeServiceABC:
    return LikeService()