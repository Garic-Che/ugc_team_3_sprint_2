from datetime import datetime, timedelta
from jose import JWTError, jwt
import uuid

from fastapi import Request, Depends, HTTPException
from http import HTTPStatus
from typing import Optional
from redis.asyncio import Redis
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from models.entity import (
    User,
    RefreshToken,
    Role,
    Privilege,
    role_privilege,
    user_role,
)
from db.postgres import get_session
from core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class AuthEngine:
    def __init__(self, redis: Redis, session: AsyncSession):
        self.redis = redis
        self.session = session

    def hash_password(self, password: str) -> str:
        """Хеширует пароль."""
        return pwd_context.hash(password)

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Проверяет, совпадает ли пароль с хешем."""
        return pwd_context.verify(plain_password, hashed_password)

    async def execute_query(self, query):
        """Выполнить запрос и вернуть результат."""
        result = await self.session.execute(query)
        return result

    async def add_object(self, obj):
        """Добавить объект в сессию и зафиксировать изменения."""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete_object(self, obj):
        await self.session.delete(obj)
        await self.session.commit()

    async def change_login(self, user_id: str, new_login: str):
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(login=new_login)
        )
        await self.session.commit()

    async def change_password(self, user_id: str, hashed_password: str):
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(password=hashed_password)
        )
        await self.session.commit()

    async def rollback(self):
        """Откатить транзакцию."""
        await self.session.rollback()

    async def get_one_or_none(self, query):
        """Выполнить запрос и вернуть один результат или None."""
        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def get_all(self, query):
        """Выполнить запрос и вернуть все результаты."""
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_name(self, model, name: str):
        """Получает объект модели по имени."""
        query = select(model).where(model.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()

    def decode_access_token(self, access_token: str) -> dict[str]:
        """Декодирует access_token и возвращает payload."""
        if not access_token:
            return None
        try:
            payload = jwt.decode(
                access_token,
                settings.auth_secret_key,
                algorithms=[settings.algorithm],
            )
            return payload
        except JWTError:
            return None

    def decode_access_token_into_id(self, access_token: str) -> Optional[str]:
        """Декодирует access_token и возвращает user_id."""
        payload = self.decode_access_token(access_token)
        if not payload:
            return None
        user_id = payload.get("user_id")
        return user_id

    def decode_access_token_into_roles(self, access_token: str) -> list[str]:
        """Декодирует access_token и возвращает roles."""
        payload = self.decode_access_token(access_token)
        if not payload:
            return []
        roles = payload.get("roles")
        return roles

    def decode_access_token_into_exp(self, access_token: str) -> Optional[str]:
        """Декодирует access_token и возвращает expired."""
        payload = self.decode_access_token(access_token)
        if not payload:
            return None
        expired = payload.get("exp")
        return expired

    async def have_privilege(
        self, access_token: str, privilege_name: str
    ) -> bool:
        """Проверяет, есть ли у пользователя указанная привилегия."""
        allow_privileges = [
            "user/register",
            "user/login",
            "user/update_access",
            "user/exit",
            "user/login/provider",
            "user/login/provider/callback",
        ]
        main_privileges = [
            "user/profile",
            "user/update_access",
            "user/exit",
            "user/change/login",
            "user/change/password",
            "user/history",
            "user/unlink",
        ]

        if privilege_name in allow_privileges:
            return True

        if not access_token:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Access token is required",
            )

        # Декодируем токен и получаем user_id
        user_id = self.decode_access_token_into_id(access_token)
        if not user_id:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid or expired access token",
            )

        if privilege_name in main_privileges:
            return True

        # Получаем роли пользователя
        role_query = select(user_role.c.role_id).where(
            user_role.c.user_id == user_id
        )
        roles = await self.get_all(role_query)

        if not roles:
            return False  # У пользователя нет ролей → нет привилегий

        # Проверка суперадмина
        if "f0a7493d-1e6b-4cdb-91f6-0f5568be51c5" in [
            str(role_id) for role_id in roles
        ]:
            return True

        # Проверяем, есть ли у ролей нужная привилегия
        privilege_query = (
            select(Privilege.id)
            .join(role_privilege)
            .where(
                role_privilege.c.role_id.in_(roles),
                Privilege.name == privilege_name,
            )
        )
        privilege = await self.get_one_or_none(privilege_query)

        return bool(privilege)

    async def get_user_by_id(self, session: AsyncSession, user_id: str) -> str:
        """Доставание из базы данных профиля пользователя по id"""
        result = await session.execute(select(User).where(User.id == user_id))
        profile = result.scalar_one_or_none()
        return profile

    def create_access_token(
        self,
        user_id: str,
        roles: list[str],
        secret_key: str,
        access_token_expires_in: int,
    ) -> dict:
        """Создание JWT-access токена"""
        payload = {
            "user_id": str(user_id),
            "roles": roles,
            "jti": str(uuid.uuid4()),
            "exp": datetime.utcnow()
            + timedelta(seconds=access_token_expires_in),
        }
        return jwt.encode(payload, secret_key, algorithm=settings.algorithm)

    async def create_refresh_token(
        self,
        session: AsyncSession,
        user_id: str,
        refresh_token_expires_in: int,
    ) -> dict:
        """Создание refresh токена"""
        refresh_token = str(uuid.uuid4())
        await self.add_refresh_token_to_db(
            session, str(user_id), refresh_token, refresh_token_expires_in
        )
        return refresh_token

    async def add_refresh_token_to_db(
        self,
        session: AsyncSession,
        user_id: str,
        refresh_token: str,
        refresh_token_expires_in: int,
    ):
        """Запись refresh токена в БД"""
        expires_at = datetime.utcnow() + timedelta(
            seconds=refresh_token_expires_in
        )
        new_token = RefreshToken(
            user_id=user_id, token=refresh_token, expired=expires_at
        )
        session.add(new_token)
        await session.commit()
        await session.refresh(new_token)

    async def _get_privileges(
        self, session: AsyncSession, privilege_ids: list[str]
    ):
        """Получаем объекты привилегий"""
        privilege_ids = set(privilege_ids)
        result = await self.session.execute(
            select(Privilege).where(Privilege.id.in_(privilege_ids))
        )
        return result

    async def _get_privileges_id(
        self, session: AsyncSession, privilege_ids: list[str]
    ):
        """Получаем объекты привилегий"""
        privilege_ids = set(privilege_ids)
        result = await self.session.execute(
            select(Privilege.id).where(Privilege.id.in_(privilege_ids))
        )
        return result

    async def _validate_privileges(
        self, session: AsyncSession, privilege_ids: list[str]
    ):
        """Проверка существования привилегий"""
        privilege_ids = set(privilege_ids)
        result = await self._get_privileges_id(
            session=session, privilege_ids=privilege_ids
        )
        exist_ids = {row[0] for row in result.scalars()}

        if len(exist_ids) != len(privilege_ids):
            invalid_ids = privilege_ids - exist_ids
            raise HTTPException(
                status_code=400,
                detail=f"Invalid privilege IDs: {', '.join(invalid_ids)}",
            )

    async def _get_roles(self, session: AsyncSession):
        """Получаем все роли"""
        result = await self.session.execute(
            select(Role).options(selectinload(Role.privileges))
        )
        roles = result.scalars().all()

        if not roles:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="No roles found"
            )

        return roles

    async def _get_role_by_id(
        self,
        session: AsyncSession,
        role_id: str,
        options=[selectinload(Role.privileges)],
    ):
        """Получить роль по идентификатору"""
        if not role_id:
            return None

        role = await self.session.get(Role, role_id, options=options)

        if not role:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Role not found"
            )
        return role

    async def _get_role_by_ids(
        self,
        session: AsyncSession,
        role_ids: list[str],
        options=selectinload(Role.privileges),
    ):
        """Получить роли по списку идентификаторов"""
        if not role_ids:
            return []

        roles_data = await self.session.execute(
            select(Role).where(Role.id.in_(role_ids)).options(options)
        )

        return roles_data.scalars().all()

    async def _delete_role_by_id(self, session: AsyncSession, role_id: str):
        if not role_id:
            return None

        # удаляем роль
        await self.session.execute(delete(Role).where(Role.id == role_id))

    async def _get_user_by_id(
        self,
        session: AsyncSession,
        user_id: str,
        options=[selectinload(User.roles)],
    ):
        """Получить пользователя по идентификатору"""
        if not user_id:
            return None

        user = await self.session.get(User, user_id, options=options)

        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="User not found"
            )

        return user

    async def get_role_names(
        self,
        user_id: str,
    ):
        """Получить пользователя по идентификатору"""
        # Получаем имена ролей пользователя
        role_query = select(Role.name).join(
            user_role, user_role.c.role_id == Role.id
        ).where(
            user_role.c.user_id == user_id
        )
        roles = await self.get_all(role_query)

        if not roles:
            return []
        return roles

    def generate_random_password(self) -> str:
        """Генерирует случайный пароль для OAuth пользователей."""
        return str(uuid.uuid4())


async def get_redis(request: Request) -> Redis:
    return request.app.state.token_engine


def get_auth_engine(
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
) -> AuthEngine:
    return AuthEngine(redis, session)
