from uuid import UUID
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from models.entity import Bookmark
from schemas.model import EntityPostDTO, EntityUpdateDTO
from services.models import UpdateModel
from services.mongo.bookmark import BookmarkServiceABC, get_bookmark_service


router = APIRouter(prefix="/bookmarks")


@router.post("/create")
async def post_bookmarks(
    request: list[EntityPostDTO],
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)]
) -> list[Bookmark]:
    bookmarks = [Bookmark(**raw.model_dump()) for raw in request]
    return await service.insert(bookmarks)


@router.get("/user/{user_id}")
async def get_user_bookmarks(
    user_id: UUID,
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)]
) -> list[Bookmark]:
    return await service.get_by_user(user_id)


@router.get("/content/{content_id}")
async def get_content_bookmarks(
    content_id: UUID,
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)]
) -> list[Bookmark]:
    return await service.get_by_content_id(content_id)


@router.get("/timerange/{start}/{end}")
async def get_timerange_bookmarks(
    start: datetime,
    end: datetime,
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)]
) -> list[Bookmark]:
    return await service.get_by_timerange(start, end)


@router.delete("/remove")
async def delete_bookmarks(
    ids: list[UUID],
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)]
) -> list[UUID]:
    return await service.delete(ids)


@router.put("/update")
async def update_bookmark(
    request: EntityUpdateDTO,
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)]
) -> Bookmark:
    update_mapping = request.model_dump(exclude_none=True, exclude_unset=True)
    return await service.update(UpdateModel(**update_mapping))
