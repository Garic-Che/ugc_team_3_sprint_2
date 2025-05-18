from uuid import UUID

from .mixin import MongoCUDMixin, MongoReadMixin
from ..base import LikeServiceABC
from ..models import LikeUpdateModel
from models.entity import Like
from exceptions.services import NotFoundKeyError


class MongoLikeService(MongoCUDMixin[Like, LikeUpdateModel], MongoReadMixin[Like], LikeServiceABC):
    def __init__(self):
        super().__init__(Like)

    async def get_avg_content_rate(self, content_id: UUID) -> float:
        avg_rate = await Like.find(
            Like.content_id == content_id
        ).avg(Like.rate)
        if not avg_rate:
            raise NotFoundKeyError([content_id])
        return avg_rate
    

def get_like_service() -> LikeServiceABC:
    return MongoLikeService()
