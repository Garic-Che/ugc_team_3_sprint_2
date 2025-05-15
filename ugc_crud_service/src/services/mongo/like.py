from .mixin import MongoCUDMixin, MongoReadMixin
from ..base import LikeServiceABC
from ..models import UpdateModel
from models.entity import Like


class MongoLikeService(MongoCUDMixin[Like, UpdateModel], MongoReadMixin[Like], LikeServiceABC):
    def __init__(self):
        super().__init__(Like)
    

def get_like_service() -> LikeServiceABC:
    return MongoLikeService()
