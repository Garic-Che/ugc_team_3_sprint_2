from uuid import UUID
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from models.entity import Bookmark
from schemas.model import EntityPostDTO, EntityUpdateDTO
from services.models import UpdateModel
from services.mongo.bookmark import BookmarkServiceABC, get_bookmark_service
from services.bearer import security_jwt


router = APIRouter(prefix="/api/v1/bookmarks")


@router.post("/create")
async def post_bookmarks(
    request: list[EntityPostDTO],
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[Bookmark]:
    user_id = user.get("user_id")
    bookmarks = [Bookmark(**raw.model_dump()) for raw in request if raw.user_id == user_id]
    return await service.insert(bookmarks)


@router.get("/user/{user_id}")
async def get_user_bookmarks(
    user_id: UUID,
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[Bookmark]:
    return await service.get_by_user(user_id)


@router.get("/content/{content_id}")
async def get_content_bookmarks(
    content_id: UUID,
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[Bookmark]:
    return await service.get_by_content_id(content_id)


@router.get("/timerange/{start}/{end}")
async def get_timerange_bookmarks(
    start: datetime,
    end: datetime,
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[Bookmark]:
    return await service.get_by_timerange(start, end)


@router.delete("/remove")
async def delete_bookmarks(
    ids: list[UUID],
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[UUID]:
    bookmarks = await service.get_by_ids(ids)
    for bookmark in bookmarks:
        if bookmark.user_id != user.get("user_id"):
            raise HTTPException(status_code=403, detail="Forbidden")
    return await service.delete(ids)


@router.put("/update")
async def update_bookmark(
    request: EntityUpdateDTO,
    service: Annotated[BookmarkServiceABC, Depends(get_bookmark_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> Bookmark:
    if request.user_id != user.get("user_id"):
        raise HTTPException(status_code=403, detail="Forbidden")
    update_mapping = request.model_dump(exclude_none=True, exclude_unset=True)
    return await service.update(UpdateModel(**update_mapping))
