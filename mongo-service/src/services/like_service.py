from uuid import UUID
from datetime import datetime
from abc import abstractmethod

from .base import CUDServiceABC, MongoCUDMixin
from .models import LikeUpdate
from models.entities import Like


class LikeServiceABC(CUDServiceABC[Like, LikeUpdate]):
    @abstractmethod
    async def get_user_likes(self, user_id: UUID) -> list[Like]:
        pass

    @abstractmethod
    async def get_content_likes(self, content_id: UUID) -> list[Like]:
        pass

    @abstractmethod
    async def get_timerange_likes(self, start: datetime, end: datetime) -> list[Like]:
        pass


class LikeService(MongoCUDMixin[Like, LikeUpdate], LikeServiceABC):
    def __init__(self):
        super().__init__(Like)

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
    

def get_like_service() -> LikeServiceABC:
    return LikeService()