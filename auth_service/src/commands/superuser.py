import typer
import asyncio
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from http import HTTPStatus

from db.postgres import async_session
from models.entity import Role, User, user_role
from db.auth_engine import AuthEngine

app = typer.Typer()

SUPERUSER_ROLE_ID = "f0a7493d-1e6b-4cdb-91f6-0f5568be51c5"
SUPERUSER_ROLE_NAME = "SUPERUSER"


class Superuser:
    def __init__(self, auth_engine, session: AsyncSession):
        self.auth_engine = auth_engine
        self.session = session

    async def ensure_superuser_role(self) -> Role:
        """Создает или возвращает роль суперадмина."""
        role = await self.session.get(Role, SUPERUSER_ROLE_ID)
        if not role:
            role = Role(id=SUPERUSER_ROLE_ID, name=SUPERUSER_ROLE_NAME)
            self.session.add(role)
            await self.session.commit()
            print(f"✔ Создана роль {SUPERUSER_ROLE_NAME}")
        return role

    async def register_admin(self, login: str, password: str) -> User:
        """Регистрация пользователя."""
        result = await self.session.execute(
            select(User).where(User.login == login)
        )
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="User with this login already exists",
            )

        hashed_password = self.auth_engine.hash_password(password)
        new_user = User(login=login, password=hashed_password)

        try:
            self.session.add(new_user)
            await self.session.commit()
            await self.session.refresh(new_user)
            return new_user

        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Error occurred while saving the user",
            )

    async def assign_su_role(self, user: User) -> str:
        """Назначить пользователю роль."""
        role = await self.session.get(Role, SUPERUSER_ROLE_ID)
        if not role:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"{SUPERUSER_ROLE_NAME} role not found",
            )

        # Проверяем существующую связь
        stmt = select(user_role).where(
            user_role.c.user_id == user.id,
            user_role.c.role_id == SUPERUSER_ROLE_ID,
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="Role already assigned"
            )

        # Добавляем связь
        stmt = user_role.insert().values(
            user_id=user.id, role_id=SUPERUSER_ROLE_ID
        )
        await self.session.execute(stmt)
        await self.session.commit()  # 🔥 Добавляем явный коммит

        return f"✔ Role {SUPERUSER_ROLE_NAME} assigned to user {user.login}"


@app.command()
def create(login: str, password: str):
    async def _execute():
        async with async_session() as session:
            # Создаем mock Redis
            class MockRedis:
                async def ping(self):
                    return True

            redis = MockRedis()
            auth_engine = AuthEngine(redis=redis, session=session)

            user_service = Superuser(auth_engine=auth_engine, session=session)

            try:
                await user_service.ensure_superuser_role()
                user = await user_service.register_admin(login, password)
                result = await user_service.assign_su_role(user)
                print(f"✅ {result}")
            except Exception as e:
                await session.rollback()
                print(f"❌ Ошибка: {str(e)}")
                raise typer.Exit(1)

    asyncio.run(_execute())


if __name__ == "__main__":
    app()
