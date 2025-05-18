from uuid import UUID
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from models.entity import Like
from schemas.model import LikePostDTO, LikeUpdateDTO
from services.models import LikeUpdateModel
from services.mongo.like import LikeServiceABC, get_like_service


router = APIRouter(prefix="/api/v1/likes")


@router.post("/create")
async def post_likes(
    request: list[LikePostDTO],
    service: Annotated[LikeServiceABC, Depends(get_like_service)]
) -> list[Like]:
    likes = [Like(**raw.model_dump()) for raw in request]
    return await service.insert(likes)


@router.get("/user/{user_id}")
async def get_user_likes(
    user_id: UUID,
    service: Annotated[LikeServiceABC, Depends(get_like_service)]
) -> list[Like]:
    return await service.get_by_user(user_id)


@router.get("/content/{content_id}")
async def get_content_likes(
    content_id: UUID,
    service: Annotated[LikeServiceABC, Depends(get_like_service)]
) -> list[Like]:
    return await service.get_by_content_id(content_id)


@router.get("/timerange/{start}/{end}")
async def get_timerange_likes(
    start: datetime,
    end: datetime,
    service: Annotated[LikeServiceABC, Depends(get_like_service)]
) -> list[Like]:
    return await service.get_by_timerange(start, end)


@router.delete("/remove")
async def delete_likes(
    ids: list[UUID],
    service: Annotated[LikeServiceABC, Depends(get_like_service)]
) -> list[UUID]:
    return await service.delete(ids)


@router.put("/update")
async def update_like(
    request: LikeUpdateDTO,
    service: Annotated[LikeServiceABC, Depends(get_like_service)]
) -> Like:
    update_mapping = request.model_dump(exclude_none=True, exclude_unset=True)
    return await service.update(LikeUpdateModel(**update_mapping))


@router.get("/avg_rate/{content_id}")
async def get_avg_content_rate(
    content_id: UUID,
    service: Annotated[LikeServiceABC, Depends(get_like_service)]
) -> float:
    avg_rate = await service.get_avg_content_rate(content_id)
    return round(avg_rate, 2)
