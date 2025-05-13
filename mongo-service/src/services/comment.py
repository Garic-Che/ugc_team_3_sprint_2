from .base import CRUDServiceABC, MongoCRUDMixin
from .models import CommentUpdateModel
from models.entities import Comment


class CommentServiceABC(CRUDServiceABC[Comment, CommentUpdateModel]):
    pass


class CommentService(MongoCRUDMixin[Comment, CommentUpdateModel], CommentServiceABC):
    def __init__(self):
        super().__init__(Comment)
    

def get_comment_service() -> CommentServiceABC:
    return CommentService()
