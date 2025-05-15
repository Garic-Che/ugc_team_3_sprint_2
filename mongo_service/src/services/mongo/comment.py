from .mixin import MongoCUDMixin, MongoReadMixin
from ..base import CommentServiceABC
from ..models import CommentUpdateModel
from models.entity import Comment


class MongoCommentService(MongoCUDMixin[Comment, CommentUpdateModel], MongoReadMixin[Comment], CommentServiceABC):
    def __init__(self):
        super().__init__(Comment)

    async def search_by_text(self, term: str) -> list[Comment]:
        comments = await Comment.find_many({'$text': {'$search': term}}).to_list()
        if not comments:
            return []
        return comments
        

def get_comment_service() -> CommentServiceABC:
    return MongoCommentService()
