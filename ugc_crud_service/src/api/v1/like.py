from uuid import UUID
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from models.entity import Like
from schemas.model import EntityPostDTO, EntityUpdateDTO
from services.models import UpdateModel
from services.mongo.like import LikeServiceABC, get_like_service
from services.bearer import security_jwt

router = APIRouter(prefix="/api/v1/likes")


@router.post("/create")
async def post_likes(
    request: list[EntityPostDTO],
    service: Annotated[LikeServiceABC, Depends(get_like_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[Like]:
    user_id = user.get("user_id")
    likes = [Like(**raw.model_dump()) for raw in request if raw.user_id == user_id]
    return await service.insert(likes)


@router.get("/user/{user_id}")
async def get_user_likes(
    user_id: UUID,
    service: Annotated[LikeServiceABC, Depends(get_like_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[Like]:
    return await service.get_by_user(user_id)


@router.get("/content/{content_id}")
async def get_content_likes(
    content_id: UUID,
    service: Annotated[LikeServiceABC, Depends(get_like_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[Like]:
    return await service.get_by_content_id(content_id)


@router.get("/timerange/{start}/{end}")
async def get_timerange_likes(
    start: datetime,
    end: datetime,
    service: Annotated[LikeServiceABC, Depends(get_like_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[Like]:
    return await service.get_by_timerange(start, end)


@router.delete("/remove")
async def delete_likes(
    ids: list[UUID],
    service: Annotated[LikeServiceABC, Depends(get_like_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> list[UUID]:
    likes = await service.get_by_ids(ids)
    for like in likes:
        if like.user_id != user.get("user_id"):
            raise HTTPException(status_code=403, detail="Forbidden")
    return await service.delete(ids)


@router.put("/update")
async def update_like(
    request: EntityUpdateDTO,
    service: Annotated[LikeServiceABC, Depends(get_like_service)],
    user: Annotated[dict, Depends(security_jwt)]
) -> Like:
    if request.user_id != user.get("user_id"):
        raise HTTPException(status_code=403, detail="Forbidden")
    update_mapping = request.model_dump(exclude_none=True, exclude_unset=True)
    return await service.update(UpdateModel(**update_mapping))
