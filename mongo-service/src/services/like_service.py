from uuid import UUID
from abc import abstractmethod

from .base import CRUDServiceABC, MongoCRUDMixin
from .models import LikeUpdate
from models.entities import Like


class LikeServiceABC(CRUDServiceABC[Like, LikeUpdate]):
    @abstractmethod
    async def get_by_content_id(self, content_id: UUID) -> list[Like]:
        pass


class LikeService(MongoCRUDMixin[Like, LikeUpdate], LikeServiceABC):
    def __init__(self):
        super().__init__(Like)

    async def get_by_content_id(self, content_id: UUID) -> list[Like]:
        content_likes = await Like.find(Like.content_id == content_id).to_list()
        if not content_likes:
            return []
        return content_likes
    

def get_like_service() -> LikeServiceABC:
    return LikeService()