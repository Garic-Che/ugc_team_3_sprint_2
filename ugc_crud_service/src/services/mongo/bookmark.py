from .mixin import MongoCUDMixin, MongoReadMixin
from ..base import BookmarkServiceABC
from ..models import UpdateModel
from models.entity import Bookmark


class MongoBookmarkService(MongoCUDMixin[Bookmark, UpdateModel], MongoReadMixin[Bookmark], BookmarkServiceABC):
    def __init__(self):
        super().__init__(Bookmark)
    

def get_bookmark_service() -> BookmarkServiceABC:
    return MongoBookmarkService()
