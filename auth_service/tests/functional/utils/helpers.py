import uuid
from datetime import datetime
import json
import base64

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlalchemy import Column, DateTime, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base


class CommonSettings(BaseSettings):
    protocol: str = Field("http://")
    host: str = ...
    port: int = ...

    def get_host(self):
        return f"{self.protocol}{self.host}:{self.port}"


class RedisSettings(BaseSettings):
    token_redis_host: str = Field(..., alias="TOKEN_REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")


class DBSettings(BaseSettings):
    pg_host: str = Field(..., alias="AUTH_DB_HOST")
    pg_port: int = Field(..., alias="AUTH_DB_PORT")
    pg_user: str = Field(..., alias="AUTH_DB_USER")
    pg_password: str = Field(..., alias="AUTH_DB_PASSWORD")
    pg_db: str = Field(..., alias="AUTH_DB_DATABASE")


class ServiceSettings(CommonSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_SERVICE_")


es_settings = DBSettings()
redis_settings = RedisSettings()
service_settings = ServiceSettings()


Base = declarative_base()
SCHEMA = "content"


class UuidCreatedMixin:
    __table_args__ = {"schema": SCHEMA}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created = Column(DateTime, default=datetime.utcnow)


user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", String, ForeignKey(f"{SCHEMA}.user.id")),
    Column("role_id", String, ForeignKey(f"{SCHEMA}.role.id")),
)


class User(UuidCreatedMixin, Base):
    __tablename__ = "user"

    login = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    modified = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    roles = relationship("Role", secondary=user_role, back_populates="users")

    def __repr__(self) -> str:
        return f"<User {self.login}>"


role_privilege = Table(
    "role_privilege",
    Base.metadata,
    Column("role_id", String, ForeignKey(f"{SCHEMA}.role.id")),
    Column("privilege_id", String, ForeignKey(f"{SCHEMA}.privilege.id")),
)


class Role(UuidCreatedMixin, Base):
    __tablename__ = "role"

    name = Column(String, nullable=False, unique=True)
    modified = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    users = relationship(
        "User", secondary=user_role, back_populates="roles"
    )  # Используем объект таблицы
    privileges = relationship(
        "Privilege", secondary=role_privilege, back_populates="roles"
    )


class Privilege(UuidCreatedMixin, Base):
    __tablename__ = "privilege"

    name = Column(String, nullable=False, unique=True)
    modified = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    roles = relationship(
        "Role", secondary=role_privilege, back_populates="privileges"
    )


class RefreshToken(UuidCreatedMixin, Base):
    __tablename__ = "refresh_token"

    user_id = Column(
        String,
        ForeignKey(f"{SCHEMA}.user.id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String, nullable=False)
    expired = Column(DateTime, nullable=False)


def create_time_partitions(
    table_name: str, 
    partition_column: str,
    partition_type: str = 'range',
    interval: str = 'monthly'
):
    """функций партицирования
    interval: daily/weekly/monthly
    partition_type: list/range/hash
    """
    def _create_partitions(target, connection, **kw):
        connection.execute(text(
            f"SELECT create_parent(:table_name, :partition_column, :partition_type, :interval);"
        ).bindparams(
            table_name=f"{SCHEMA}.{table_name}",
            partition_column=partition_column,
            partition_type=partition_type,
            interval=interval
        ))
    
    return _create_partitions

class History(Base):
    __tablename__ = "history"
    __table_args__ = {
        "schema": SCHEMA,
        'postgresql_partition_by': 'RANGE (entered)',
        'listeners': [
            ('after_create', create_time_partitions(
                table_name="history",
                partition_column="entered"
            ))
        ],
    }

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey(f"{SCHEMA}.user.id", ondelete="CASCADE"))
    user_agent = Column(String, nullable=False)
    entered = Column(DateTime, primary_key=True, default=datetime.utcnow)   # добавляем pk
    user_device_type = Column(String, nullable=True)


def get_state_from_session(session_cookie: str) -> str:
    """Извлекает state из сессионной cookie."""
    try:
        # Декодируем JWT токен сессии
        parts = session_cookie.split(".")
        if len(parts) != 3:
            return None

        # Декодируем payload
        payload = json.loads(
            base64.b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
        )

        # Получаем state из данных сессии
        for key, value in payload.items():
            if key.startswith("_state_google_"):
                return key.split("_state_google_")[1]
    except Exception:
        return None
    return None
