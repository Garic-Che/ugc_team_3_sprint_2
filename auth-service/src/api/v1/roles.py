from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request

from services.role import RoleService, get_role_service
from api.v1.schemes import CommonID, Message, Role, RoleWithID, RoleResponse
from utils.authtorize_helpers import check_privilege


router = APIRouter()


@router.post(
    "/create",
    response_model=RoleWithID,
    summary="Создание роли",
)
@check_privilege("role/create")
async def create_role(
    request: Request,
    data: Role,
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    role = await service.create_role(
        name=data.name, privilege_ids=data.privilege_ids
    )
    return RoleResponse(
        id=role.id,
        name=role.name,
        created=role.created,
        modified=role.modified,
        privilege_ids=[p.id for p in role.privileges],
    )


@router.delete(
    "/delete",
    response_model=Message,
    summary="Удаление роли",
)
@check_privilege("role/delete")
async def delete_role(
    request: Request,
    data: CommonID,
    service: RoleService = Depends(get_role_service),
) -> Message:
    msg = await service.delete_role(data.id)
    if not msg:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="bad request"
        )

    return Message(detail=msg)


@router.put(
    "/change",
    response_model=RoleWithID,
    summary="Изменение роли",
)
@check_privilege("role/change")
async def change_role(
    request: Request,
    data: RoleWithID,
    service: RoleService = Depends(get_role_service),
) -> RoleWithID:
    retval = await service.change_role(data.id, data.name, data.privilege_ids)
    if not retval:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="bad request"
        )

    return RoleWithID(
        id=retval.get("id"),
        name=retval.get("name"),
        privilege_ids=retval.get("privileges"),
    )


@router.get(
    "/",
    response_model=list[RoleWithID],
    summary="Все роли",
)
@check_privilege("role/")
async def all_roles(
    request: Request,
    service: RoleService = Depends(get_role_service),
) -> list[RoleWithID]:
    roles = await service.all_roles()
    return [
        RoleWithID(
            id=role.get("id"),
            name=role.get("name"),
            privilege_ids=role.get("privileges"),
        )
        for role in roles
    ]


@router.post(
    "/assign/{user_id}",
    response_model=Message,
    summary="Назначить пользователю роль",
)
@check_privilege("role/assign")
async def assign_role(
    request: Request,
    user_id: str,
    data: CommonID,
    service: RoleService = Depends(get_role_service),
) -> Message:
    msg = await service.assign_role(data.id, user_id)
    if not msg:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="bad request"
        )

    return Message(detail=msg)


@router.post(
    "/revoke/{user_id}",
    response_model=Message,
    summary="Отобрать у пользователя роль",
)
@check_privilege("role/revoke")
async def revoke_role(
    request: Request,
    user_id: str,
    data: CommonID,
    service: RoleService = Depends(get_role_service),
) -> Message:
    msg = await service.revoke_role(data.id, user_id)
    if not msg:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="bad request"
        )

    return Message(detail=msg)


@router.get(
    "/{user_id}",
    response_model=list[RoleWithID],
    summary="Получение списка ролей пользователя",
)
@check_privilege("role/user")
async def all_roles_user(
    request: Request,
    user_id: str,
    service: RoleService = Depends(get_role_service),
) -> list[RoleWithID]:
    # Получаем роли пользователя из сервиса
    roles = await service.all_roles_user(user_id)

    # Если ролей нет, выбрасываем исключение
    if not roles:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Not found"
        )

    # Возвращаем роли в формате Pydantic модели
    return [
        RoleWithID(
            id=role.get("id"),
            name=role.get("name"),
            privilege_ids=role.get("privileges"),
        )
        for role in roles
    ]
