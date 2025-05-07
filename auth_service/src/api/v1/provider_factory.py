from http import HTTPStatus
from abc import ABC, abstractmethod
from typing import Dict, Any

from fastapi import HTTPException, Request
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config


class OAuthProvider(ABC):
    @abstractmethod
    async def authorize_redirect(self, request: Request, redirect_uri: str):
        pass

    @abstractmethod
    async def authorize_access_token(self, request: Request) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_user_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_email(self, token: Dict[str, Any]) -> str:
        pass


class GoogleOAuthProvider(OAuthProvider):
    def __init__(self):
        config = Config(".env")
        self.oauth = OAuth(config)
        self.oauth.register(
            name="google",
            server_metadata_url=(
                "https://accounts.google.com/.well-known/openid-configuration"
            ),
            client_kwargs={"scope": "openid email profile"},
        )

    async def authorize_redirect(self, request: Request, redirect_uri: str):
        return await self.oauth.google.authorize_redirect(
            request, redirect_uri
        )

    async def authorize_access_token(self, request: Request) -> Dict[str, Any]:
        return await self.oauth.google.authorize_access_token(request)

    async def get_user_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        return token.get("userinfo", {})

    async def get_email(self, token: Dict[str, Any]) -> str:
        user_info = await self.get_user_info(token)
        return user_info.get("email", None)


class YandexOAuthProvider(OAuthProvider):
    def __init__(self):
        config = Config(".env")
        self.oauth = OAuth(config)
        self.oauth.register(
            name="yandex",
            authorize_url="https://oauth.yandex.ru/authorize",
            access_token_url="https://oauth.yandex.ru/token",
            client_kwargs={
                "scope": "login:email login:info",
                "token_endpoint_auth_method": "client_secret_post",
            },
        )

    async def authorize_redirect(self, request: Request, redirect_uri: str):
        return await self.oauth.yandex.authorize_redirect(
            request, redirect_uri
        )

    async def authorize_access_token(self, request: Request) -> Dict[str, Any]:
        return await self.oauth.yandex.authorize_access_token(request)

    async def get_user_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self.oauth.yandex.get(
            "https://login.yandex.ru/info", token=token
        )
        if resp.status_code != HTTPStatus.OK:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Failed to get user info from Yandex",
            )

        return resp.json()

    async def get_email(self, token: Dict[str, Any]) -> str:
        user_info = await self.get_user_info(token)
        return user_info.get("default_email", None)


class VkOAuthProvider(OAuthProvider):
    def __init__(self):
        config = Config(".env")
        self.VK_CLIENT_ID = config("VK_CLIENT_ID")
        self.oauth = OAuth(config)
        self.oauth.register(
            name="vk",
            client_id=self.VK_CLIENT_ID,
            access_token_url="https://id.vk.com/oauth2/auth",
            authorize_url="https://id.vk.com/authorize",
            api_base_url="https://id.vk.com/oauth2/",
            client_kwargs={"code_challenge_method": "S256", "scope": "email"},
        )

    async def authorize_redirect(self, request: Request, redirect_uri: str):
        return await self.oauth.vk.authorize_redirect(request, redirect_uri)

    async def authorize_access_token(self, request: Request) -> Dict[str, Any]:
        return await self.oauth.vk.authorize_access_token(
            request,
            device_id=request.query_params.get("device_id"),
            client_id=self.VK_CLIENT_ID,
        )

    async def get_user_info(self, token: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.oauth.vk.post(
            "user_info",
            token=token,
            params={"client_id": self.VK_CLIENT_ID},
        )

        if not result.json() or not result.json()["user"]:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Failed to fetch user data",
            )

        return result.json()["user"]

    async def get_email(self, token: Dict[str, Any]) -> str:
        user_info = await self.get_user_info(token)
        return user_info.get("email", None)


class OAuthProviderFactory:
    @staticmethod
    def create_provider(provider_name: str) -> OAuthProvider:
        providers = {
            "google": GoogleOAuthProvider,
            "yandex": YandexOAuthProvider,
            "vk": VkOAuthProvider,
        }

        if provider_name not in providers:
            raise ValueError(f"Unsupported provider: {provider_name}")

        return providers[provider_name]()
