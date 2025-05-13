from uuid import UUID
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from models.entity import Comment
from schemas.model import CommentPostDTO, CommentUpdateDTO
from services.models import CommentUpdateModel
from services.mongo.comment import CommentServiceABC, get_comment_service


router = APIRouter(prefix="/comments")


@router.post("/create")
async def post_comments(
    request: list[CommentPostDTO],
    service: Annotated[CommentServiceABC, Depends(get_comment_service)]
) -> list[Comment]:
    comments = [Comment(**raw.model_dump()) for raw in request]
    return await service.insert(comments)


@router.get("/user/{user_id}")
async def get_user_comments(
    user_id: UUID,
    service: Annotated[CommentServiceABC, Depends(get_comment_service)]
) -> list[Comment]:
    return await service.get_by_user(user_id)


@router.get("/content/{content_id}")
async def get_content_comments(
    content_id: UUID,
    service: Annotated[CommentServiceABC, Depends(get_comment_service)]
) -> list[Comment]:
    return await service.get_by_content_id(content_id)


@router.get("/timerange/{start}/{end}")
async def get_timerange_comments(
    start: datetime,
    end: datetime,
    service: Annotated[CommentServiceABC, Depends(get_comment_service)]
) -> list[Comment]:
    return await service.get_by_timerange(start, end)


@router.delete("/remove")
async def delete_comments(
    ids: list[UUID],
    service: Annotated[CommentServiceABC, Depends(get_comment_service)]
) -> list[UUID]:
    return await service.delete(ids)


@router.put("/update")
async def update_comment(
    request: CommentUpdateDTO,
    service: Annotated[CommentServiceABC, Depends(get_comment_service)]
) -> Comment:
    update_mapping = request.model_dump(exclude_none=True, exclude_unset=True)
    return await service.update(CommentUpdateModel(**update_mapping))
