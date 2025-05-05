from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from utils.jwt_helpers import decode_token
from utils.authtorize_helpers import (
    check_privilege,
    check_access_token,
    validate_user,
    validate_password,
)
from services.user import UserService, get_user_service
from api.v1.schemes import (
    Entrance,
    Message,
    NewLogin,
    NewPassword,
    UpdateAccess,
    User,
    UserAuth,
    CommonID,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=CommonID,
    summary="Регистрация пользователя",
)
@check_privilege("user/register")
async def register_user(
    request: Request,
    data: UserAuth,
    service: UserService = Depends(get_user_service),
) -> CommonID:
    user_id = await service.register_user(data.login, data.password)

    if not user_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="User not registered"
        )

    return CommonID(id=user_id)


@router.post(
    "/login",
    response_model=Message,
    summary="Вход пользователя",
    responses={
        200: {
            "description": "Успешный вход",
            "headers": {
                "Set-Cookie": {
                    "description": "Устанавливает access_token и refresh_token",
                    "schema": {
                        "type": "string",
                        "example": "access_token=...; Path=/; HttpOnly; SameSite=Strict",
                    },
                }
            },
        }
    },
)
@check_privilege("user/login")
async def enter_user(
    request: Request,
    response: Response,
    data: UserAuth,
    service: UserService = Depends(get_user_service),
) -> Message:
    msg = await service.enter_user(
        request, response, data.login, data.password
    )
    if not msg:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="User not entered"
        )

    return Message(detail=msg)


@router.get(
    "/",
    response_model=User,
    summary="Профиль пользователя",
)
@router.get(
    "/profile",
    response_model=User,
    summary="Профиль пользователя",
)
@check_access_token
@check_privilege("user/profile")
async def user_profile(
    request: Request,
    service: UserService = Depends(get_user_service),
) -> User:
    user = await service.get_user_profile(request)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    return User(
        id=user.id,
        login=user.login,
        created=user.created,
    )


@router.post(
    "/update_access",
    response_model=UpdateAccess,
    summary="Продление доступа",
    responses={
        200: {
            "description": "Успешное обновление токенов",
            "headers": {
                "Set-Cookie": {
                    "description": "Обновляет access_token и refresh_token",
                    "schema": {
                        "type": "string",
                        "example": "access_token=...; Path=/; HttpOnly; SameSite=Strict",
                    },
                }
            },
        }
    },
)
@check_privilege("user/update_access")
async def update_access(
    request: Request,
    response: Response,
    service: UserService = Depends(get_user_service),
) -> UpdateAccess:
    new_access = await service.user_update_access(request, response)
    if not new_access:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Access not updated"
        )

    return UpdateAccess(
        refresh_token=new_access["refresh_token"],
        access_token=new_access["access_token"],
    )


@router.post(
    "/exit",
    response_model=Message,
    summary="Выход пользователя",
    responses={
        200: {
            "description": "Успешный выход",
            "headers": {
                "Set-Cookie": {
                    "description": "Удаляет access_token и refresh_token",
                    "schema": {
                        "type": "string",
                        "example": "access_token=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0",
                    },
                }
            },
        }
    },
)
@check_access_token
@check_privilege("user/exit")
async def exit_user(
    request: Request,
    response: Response,
    service: UserService = Depends(get_user_service),
) -> Message:
    msg = await service.exit_user(response)
    if not msg:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Bad request"
        )

    return Message(detail=msg)


@router.put(
    "/change/login",
    response_model=Message,
    summary="Замена логина",
)
@check_access_token
@check_privilege("user/change/login")
async def change_login(
    request: Request,
    data: NewLogin,
    service: UserService = Depends(get_user_service),
) -> Message:
    # достаем user_id
    payload = decode_token(request.cookies.get("access_token"))
    if not payload:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token"
        )

    validate_user(data.new_login)

    msg = await service.change_login(payload["user_id"], data.new_login)
    if not msg:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Login not changed"
        )

    return Message(detail=msg)


@router.put(
    "/change/password",
    response_model=Message,
    summary="Замена пароля",
)
@check_access_token
@check_privilege("user/change/password")
async def change_password(
    request: Request,
    data: NewPassword,
    service: UserService = Depends(get_user_service),
) -> Message:
    payload = decode_token(request.cookies.get("access_token"))
    if not payload:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token"
        )

    validate_password(data.new_password)

    msg = await service.change_password(
        payload["user_id"], data.old_password, data.new_password
    )
    if not msg:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Password not changed"
        )

    return Message(detail=msg)


@router.get(
    "/history",
    response_model=list[Entrance],
    summary="Получение истории входов пользователя",
)
@check_access_token
@check_privilege("user/history")
async def user_history(
    request: Request,
    page: int = Query(1, description="Номер страницы", gt=0),
    per_page: int = Query(
        10, description="Количество записей на странице", gt=0, le=100
    ),
    service: UserService = Depends(get_user_service),
) -> list[Entrance]:
    entrances = await service.user_history(
        request, page=page, per_page=per_page
    )
    if not entrances:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Not found"
        )

    return [
        Entrance(
            timestamp=entrance.entered.isoformat(),
            user_agent=entrance.user_agent,
        )
        for entrance in entrances
    ]


@router.get(
    "/unlink",
    response_model=UserAuth,
    summary="Отвязка внешнего аккаунта",
)
@check_access_token
@check_privilege("user/unlink")
async def user_unlink(
    request: Request,
    service: UserService = Depends(get_user_service),
) -> UserAuth:
    user_data = await service.user_unlink(request)
    if not user_data:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="User not unlinked"
        )

    return UserAuth(
        login=user_data["login"],
        password=user_data["password"],
    )
