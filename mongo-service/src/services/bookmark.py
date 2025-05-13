from .base import CRUDServiceABC, MongoCRUDMixin
from .models import UpdateModel
from models.entities import Bookmark


class BookmarkServiceABC(CRUDServiceABC[Bookmark, UpdateModel]):
    pass


class BookmarkService(MongoCRUDMixin[Bookmark, UpdateModel], BookmarkServiceABC):
    def __init__(self):
        super().__init__(Bookmark)
    

def get_bookmark_service() -> BookmarkServiceABC:
    return BookmarkService()
