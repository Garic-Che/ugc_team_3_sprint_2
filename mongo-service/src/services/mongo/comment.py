from .mixin import MongoCUDMixin, MongoReadMixin
from ..base import CommentServiceABC
from ..models import CommentUpdateModel
from models.entity import Comment


class MongoCommentService(MongoCUDMixin[Comment, CommentUpdateModel], MongoReadMixin[Comment], CommentServiceABC):
    def __init__(self):
        super().__init__(Comment)
    

def get_comment_service() -> CommentServiceABC:
    return MongoCommentService()
