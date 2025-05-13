from uuid import UUID
from abc import abstractmethod

from .base import CRUDServiceABC, MongoCRUDMixin
from .models import BookmarkUpdate
from models.entities import Bookmark


class BookmarkServiceABC(CRUDServiceABC[Bookmark, BookmarkUpdate]):
    @abstractmethod
    async def get_by_content_id(self, content_id: UUID) -> list[Bookmark]:
        pass


class BookmarkService(MongoCRUDMixin[Bookmark, BookmarkUpdate], BookmarkServiceABC):
    def __init__(self):
        super().__init__(Bookmark)
    
    async def get_by_content_id(self, content_id: UUID) -> list[Bookmark]:
        content_bookmarks = await Bookmark.find(Bookmark.content_id == content_id).to_list()
        if not content_bookmarks:
            return []
        return content_bookmarks
    

def get_bookmark_service() -> BookmarkServiceABC:
    return BookmarkService()
