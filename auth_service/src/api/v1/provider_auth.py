from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from authlib.integrations.starlette_client import OAuthError
from starlette.config import Config
from fastapi_limiter.depends import RateLimiter

from utils.authtorize_helpers import check_privilege
from services.user import UserService, get_user_service
from api.v1.schemes import Message
from api.v1.provider_factory import OAuthProviderFactory

config = Config(".env")
LIMITER_PERIOD = config("LIMITER_PERIOD_IN_SEC", int)
REQUESTS_PER_PERIOD = config("LIMITER_REQUESTS_PER_PERIOD", int)

router = APIRouter()


@router.get(
    "/login/{provider}",
    summary="Вход через провайдер аутентификации",
    dependencies=[
        Depends(RateLimiter(times=REQUESTS_PER_PERIOD, seconds=LIMITER_PERIOD))
    ],
)
@check_privilege("user/login/provider")
async def provider_login(
    request: Request,
    provider: str,
    service: UserService = Depends(get_user_service),
) -> Message:
    try:
        provider_instance = OAuthProviderFactory.create_provider(provider)
    except (AttributeError, ValueError) as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Provider {provider} not supported: {str(e)}",
        )
    redirect_uri = request.url_for("provider_callback", provider=provider)
    return await provider_instance.authorize_redirect(request, redirect_uri)


@router.get(
    "/login/{provider}/callback",
    response_model=Message,
    summary="Callback для входа через провайдер аутентификации",
    dependencies=[
        Depends(RateLimiter(times=REQUESTS_PER_PERIOD, seconds=LIMITER_PERIOD))
    ],
)
@check_privilege("user/login/provider/callback")
async def provider_callback(
    request: Request,
    response: Response,
    provider: str,
    service: UserService = Depends(get_user_service),
) -> Message:
    try:
        provider_instance = OAuthProviderFactory.create_provider(provider)
    except (AttributeError, ValueError) as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Provider {provider} not supported: {str(e)}",
        )

    try:
        token = await provider_instance.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=f"OAuth error: {e}",
        )

    email = await provider_instance.get_email(token)
    if not email or not isinstance(email, str):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Email not provided by {provider}",
        )

    msg = await service.external_provider_auth(request, response, email)
    if not msg:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Failed to authenticate with {provider}",
        )

    return Message(detail=msg)
