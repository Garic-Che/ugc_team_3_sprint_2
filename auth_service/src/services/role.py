from functools import lru_cache
from typing import Optional
from http import HTTPStatus

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

from models.entity import Role
from db.postgres import get_session
from db.auth_engine import AuthEngine, get_auth_engine


class RoleService:
    def __init__(self, auth_engine: AuthEngine, session: AsyncSession):
        self.auth_engine = auth_engine
        self.session = session

    async def create_role(self, name: str, privilege_ids: list) -> Role:
        """Создание роли."""
        # валидируем привилегии
        await self.auth_engine._validate_privileges(
            session=self.session, privilege_ids=privilege_ids
        )

        try:
            # получаем привилегии
            privileges = await self.auth_engine._get_privileges(
                session=self.session, privilege_ids=privilege_ids
            )

            new_role = Role(name=name, privileges=privileges.scalars().all())

            self.session.add(new_role)
            await self.session.commit()
            await self.session.refresh(new_role, ["privileges"])

            return new_role

        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Role name already exists",
            )

    async def delete_role(self, role_id: str) -> Optional[str]:
        """Удаление роли."""
        try:
            # удаляем роль
            await self.auth_engine._delete_role_by_id(
                session=self.session, role_id=role_id
            )

        except IntegrityError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Cannot delete role with associated users",
            )

        return "Role deleted successfully"

    async def change_role(
        self, role_id: str, name: str, privilege_ids: list
    ) -> Optional[dict]:
        """Изменение роли."""
        # валидируем привилегии
        await self.auth_engine._validate_privileges(
            session=self.session, privilege_ids=privilege_ids
        )

        # получаем роль
        role = await self.auth_engine._get_role_by_id(
            session=self.session, role_id=role_id
        )

        try:
            if name:
                role.name = name

            # получаем и обновляем привилегии
            new_privileges = await self.auth_engine._get_privileges(
                session=self.session, privilege_ids=privilege_ids
            )
            new_privileges = new_privileges.scalars().all()

            role.privileges = new_privileges

            await self.session.refresh(role, ["privileges"])

            return {
                "id": role.id,
                "name": role.name,
                "privileges": [p.id for p in role.privileges],
            }

        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Role name already exists",
            )

    async def all_roles(self) -> list[Role]:
        """Все роли."""
        # получаем все роли
        roles = await self.auth_engine._get_roles(session=self.session)

        return [
            {
                "id": role.id,
                "name": role.name,
                "privileges": [p.id for p in role.privileges],
            }
            for role in roles
        ]

    async def assign_role(self, role_id: str, user_id: str) -> Optional[str]:
        """Назначить пользователю роль (many-to-many через user_role)."""
        # получаем пользователя
        user = await self.auth_engine._get_user_by_id(
            session=self.session, user_id=user_id
        )

        # получаем роль
        role = await self.auth_engine._get_role_by_id(
            session=self.session, role_id=role_id, options=None
        )

        # проверяем роль у пользователя
        if role in user.roles:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Role already assigned",
            )

        # добавляем роль пользователю
        user.roles.append(role)

        return f"Role {role_id} assigned to user {user_id}"

    async def revoke_role(self, role_id: str, user_id: str) -> Optional[str]:
        """Отобрать у пользователя роль."""
        # получить пользователя
        user = await self.auth_engine._get_user_by_id(
            session=self.session, user_id=user_id
        )

        # получить роль
        role = await self.auth_engine._get_role_by_id(
            session=self.session, role_id=role_id, options=None
        )

        # проверяем роль у пользователя
        if role not in user.roles:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Role not assigned to user",
            )

        # отобрать роль у пользователя
        user.roles.remove(role)

        return f"Role {role_id} revoked from user {user_id}"

    async def all_roles_user(self, user_id: str) -> list[dict]:
        """Получение списка ролей пользователя."""
        # Получаем пользователя с загруженными ролями
        user = await self.auth_engine._get_user_by_id(
            session=self.session, user_id=user_id
        )

        # получаем роли пользователя
        roles = [role.id for role in user.roles] if user else []

        # полуачем роли по списку из базы
        roles = await self.auth_engine._get_role_by_ids(
            session=self.session, role_ids=roles
        )

        return [
            {
                "id": role.id,
                "name": role.name,
                "privileges": [p.id for p in role.privileges],
            }
            for role in roles
        ]


@lru_cache()
def get_role_service(
    session: AsyncSession = Depends(get_session),
    auth_engine: AuthEngine = Depends(get_auth_engine),
) -> RoleService:
    return RoleService(auth_engine=auth_engine, session=session)
