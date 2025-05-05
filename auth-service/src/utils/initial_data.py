import logging
from sqlalchemy.future import select

from models.entity import Role, Privilege, role_privilege
from db.auth_engine import AuthEngine

DEFAULT_ROLES = {
    "ADMIN": [
        "role/create",
        "role/delete",
        "role/change",
        "role/",
        "role/user",
        "role/assign",
        "role/revoke",
    ],
    "USER": [],
    "GUEST": [],
}

DEFAULT_PRIVILEGES = [
    "role/create",
    "role/delete",
    "role/change",
    "role/",
    "role/user",
    "role/assign",
    "role/revoke",
]


async def init_roles_and_privileges(auth_engine: AuthEngine):
    # Создаем привилегии
    for priv_name in DEFAULT_PRIVILEGES:
        existing_priv = await auth_engine.session.execute(
            select(Privilege).where(Privilege.name == priv_name)
        )
        if not existing_priv.scalar_one_or_none():
            privilege = Privilege(name=priv_name)
            auth_engine.session.add(privilege)
            await auth_engine.session.commit()
            logging.info(f"Добавлена привилегия: {priv_name}")

    # Создаем роли и связываем с привилегиями
    for role_name, priv_names in DEFAULT_ROLES.items():
        # Проверяем существование роли
        existing_role = await auth_engine.session.execute(
            select(Role).where(Role.name == role_name)
        )
        role = existing_role.scalar_one_or_none()

        if not role:
            role = Role(name=role_name)
        auth_engine.session.add(role)
        await auth_engine.session.commit()
        logging.info(f"Добавлена роль: {role_name}")

        # Получаем все привилегии для роли
        privileges = []
        for priv_name in priv_names:
            privilege = await auth_engine.session.execute(
                select(Privilege).where(Privilege.name == priv_name)
            )
            privilege = privilege.scalar_one_or_none()
            if privilege:
                privileges.append(privilege)

        # Очищаем старые привилегии и добавляем новые
        await auth_engine.session.execute(
            role_privilege.delete().where(role_privilege.c.role_id == role.id)
        )

        for privilege in privileges:
            await auth_engine.session.execute(
                role_privilege.insert().values(
                    role_id=role.id, privilege_id=privilege.id
                )
            )

        await auth_engine.session.commit()
