from .base import CRUDServiceABC, MongoCRUDMixin
from .models import UpdateModel
from models.entities import Like


class LikeServiceABC(CRUDServiceABC[Like, UpdateModel]):
    pass


class LikeService(MongoCRUDMixin[Like, UpdateModel], LikeServiceABC):
    def __init__(self):
        super().__init__(Like)
    

def get_like_service() -> LikeServiceABC:
    return LikeService()