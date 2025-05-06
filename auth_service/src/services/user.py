from typing import Optional
from http import HTTPStatus
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from functools import lru_cache
from fastapi import Request, Response, Depends, HTTPException

from models.entity import User, RefreshToken, History
from db.postgres import get_session
from db.auth_engine import AuthEngine, get_auth_engine
from core.config import settings


class UserService:
    def __init__(self, auth_engine: AuthEngine, session: AsyncSession):
        self.auth_engine = auth_engine
        self.session = session

    async def register_user(self, login: str, password: str) -> Optional[str]:
        """Регистрация пользователя."""
        existing_user = await self.auth_engine.get_one_or_none(
            select(User).filter_by(login=login)
        )
        if existing_user:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="User with this login already exists",
            )

        hashed_password = self.auth_engine.hash_password(password)
        new_user = User(login=login, password=hashed_password)

        try:
            await self.auth_engine.add_object(new_user)
            return new_user.id
        except IntegrityError:
            await self.auth_engine.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Error occurred while saving the user",
            )

    async def enter_user(
        self, request: Request, response: Response, login: str, password: str
    ) -> Optional[str]:
        """Вход пользователя."""
        # Обмен логина и пароля на пару токенов:
        # JWT-access токен и refresh токен
        user = await self.auth_engine.get_one_or_none(
            select(User).filter_by(login=login)
        )
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Wrong login",
            )

        # Проверяем пароль
        if not self.auth_engine.verify_password(password, user.password):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Wrong password",
            )
        await self._enter_verified_user(request, response, user)
        return "User entered"

    async def _enter_verified_user(
        self, request: Request, response: Response, user: User
    ) -> bool:
        # Получаем роли пользователя
        user_roles = await self.auth_engine.get_role_names(user.id)

        # Создаем токены
        tokens = {}
        tokens["access_token"] = self.auth_engine.create_access_token(
            user.id,
            user_roles,
            settings.auth_secret_key,
            settings.access_token_expires_in,
        )
        tokens["refresh_token"] = await self.auth_engine.create_refresh_token(
            self.session,
            user.id,
            settings.refresh_token_expires_in,
        )

        # Получаем user-agent из заголовков
        user_agent = request.headers.get("user-agent", "unknown")

        # Сохраняем историю входа
        history_entry = History(
            user_id=user.id, user_agent=user_agent, entered=datetime.utcnow()
        )
        await self.auth_engine.add_object(history_entry)
        # Ключи вносим в куки
        expires_in = {
            "access_token": settings.access_token_expires_in,
            "refresh_token": settings.refresh_token_expires_in,
        }

        # Ключи вносим в куки
        for token_name in tokens:
            response.set_cookie(
                token_name,
                tokens[token_name],
                expires=expires_in[token_name],
                httponly=True,
            )
        return True

    async def user_update_access(
        self, request: Request, response: Response
    ) -> dict[str, str]:
        """Продление доступа."""
        r_token = request.cookies.get("refresh_token")
        refresh_token_form_bd: RefreshToken = (
            await self.auth_engine.get_one_or_none(
                select(RefreshToken).filter_by(token=r_token)
            )
        )
        if not refresh_token_form_bd:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Refresh token not found",
            )
        await self.auth_engine.delete_object(refresh_token_form_bd)
        roles = await self.auth_engine.get_role_names(
            refresh_token_form_bd.user_id
        )
        tokens = {
            "access_token": self.auth_engine.create_access_token(
                refresh_token_form_bd.user_id,
                roles,
                settings.auth_secret_key,
                settings.access_token_expires_in,
            ),
            "refresh_token": await self.auth_engine.create_refresh_token(
                self.session,
                refresh_token_form_bd.user_id,
                settings.refresh_token_expires_in,
            ),
        }

        expires_in = {
            "access_token": settings.access_token_expires_in,
            "refresh_token": settings.refresh_token_expires_in,
        }

        # Ключи вносим в куки
        for token_name in tokens:
            response.set_cookie(
                token_name,
                tokens[token_name],
                expires=expires_in[token_name],
                httponly=True,
            )

        return tokens

    async def get_user_profile(self, request: Request) -> Optional[User]:
        """Возвращает данные профиля пользователя."""
        access_token = request.cookies.get("access_token")
        user_id = self.auth_engine.decode_access_token_into_id(access_token)
        user = await self.auth_engine.get_user_by_id(self.session, user_id)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="User does not exist",
            )

        return user

    async def exit_user(self, response: Response) -> Optional[str]:
        """Выход пользователя."""
        for token_name in ["access_token", "refresh_token"]:
            response.delete_cookie(
                token_name,
                httponly=True,
            )
        return "User exited"

    async def change_login(
        self, user_id: str, new_login: str
    ) -> Optional[str]:
        """Замена логина."""
        # проверка пользователя в базе со старым именем
        exist_user = await self.auth_engine.get_one_or_none(
            select(User.id).where(User.login == new_login)
        )
        if exist_user:
            return False

        # Обновление логина
        try:
            await self.auth_engine.change_login(user_id, new_login)
        except IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Login update failed",
            )

        return "Login changed"

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> Optional[str]:
        """Замена пароля."""
        # Получаем текущий хеш пароля из БД
        stored_hash = await self.auth_engine.get_one_or_none(
            select(User.password).where(User.id == user_id)
        )
        if not stored_hash:
            return False

        # Проверяем веденный старый пароль с паролем в базе
        if not self.auth_engine.verify_password(old_password, stored_hash):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Wrong old password",
            )

        # Хешируем и сохраняем новый пароль
        hashed_password = self.auth_engine.hash_password(new_password)
        try:
            await self.auth_engine.change_password(user_id, hashed_password)
        except IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Password update failed",
            )

        return "Password changed"

    async def user_history(
        self, request: Request, page: int = 1, per_page: int = 10
    ) -> Optional[dict[str, str]]:
        """Получение истории входов пользователя с пагинацией."""
        access_token = request.cookies.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Wrong access token",
            )

        user_id = self.auth_engine.decode_access_token_into_id(access_token)

        # Вычисляем offset для пагинации
        offset = (page - 1) * per_page

        # Добавляем пагинацию к запросу
        query = (
            select(History)
            .filter_by(user_id=user_id)
            .offset(offset)
            .limit(per_page)
        )
        history = await self.auth_engine.get_all(query)

        if not history:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="History of this user does not exist",
            )

        return history

    async def user_unlink(
        self, request: Request
    ) -> dict[str, str]:
        """Отвязка внешнего аккаунта."""
        access_token = request.cookies.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Wrong access token",
            )
        user_id = self.auth_engine.decode_access_token_into_id(access_token)
        user = await self.auth_engine.get_user_by_id(self.session, user_id)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="User does not exist",
            )
        login = user.login

        # Генерируем, хешируем и сохраняем новый пароль
        generated_password = self.auth_engine.generate_random_password()
        hashed_password = self.auth_engine.hash_password(generated_password)
        try:
            await self.auth_engine.change_password(user_id, hashed_password)
        except IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Password update failed",
            )

        return {"login": login, "password": generated_password}

    async def external_provider_auth(
        self, request: Request, response: Response, email: str
    ) -> Optional[str]:
        """Аутентификация пользователя через Google."""
        # Проверяем, существует ли пользователь с таким email
        user = await self.auth_engine.get_one_or_none(
            select(User).filter_by(login=email)
        )

        if not user:
            # Если пользователь не существует, создаем нового
            password = self.auth_engine.generate_random_password()
            user_id = await self.register_user(login=email, password=password)
            if not user_id:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail="Failed to register user",
                )
            # Получаем созданного пользователя
            user = await self.auth_engine.get_one_or_none(
                select(User).filter_by(id=user_id)
            )
            if not user:
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail="Failed to get created user",
                )

        # Совершаем вход пользователя
        await self._enter_verified_user(request, response, user)
        return "Successfully authenticated"


@lru_cache()
def get_user_service(
    session: AsyncSession = Depends(get_session),
    auth_engine: AuthEngine = Depends(get_auth_engine),
) -> UserService:
    return UserService(auth_engine=auth_engine, session=session)
