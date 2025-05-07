import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy import Column, DateTime, String, ForeignKey, Table, MetaData
from sqlalchemy.orm import relationship

from db.postgres import Base

# Указываем схему для всех таблиц
SCHEMA = "content"

Base.metadata = MetaData(schema=SCHEMA)


class UuidCreatedMixin:
    __table_args__ = {"schema": SCHEMA}

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created = Column(DateTime, default=datetime.utcnow)


user_role = Table(
    "user_role",
    Base.metadata,
    Column(
        "user_id", String, ForeignKey(f"{SCHEMA}.user.id", ondelete="CASCADE")
    ),
    Column(
        "role_id", String, ForeignKey(f"{SCHEMA}.role.id", ondelete="CASCADE")
    ),
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
    Column(
        "role_id", String, ForeignKey(f"{SCHEMA}.role.id", ondelete="CASCADE")
    ),
    Column(
        "privilege_id",
        String,
        ForeignKey(f"{SCHEMA}.privilege.id", ondelete="CASCADE"),
    ),
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

    user_id = Column(String, ForeignKey(f"{SCHEMA}.user.id"), nullable=False)
    token = Column(String, nullable=False)
    expired = Column(DateTime, nullable=False)


def create_time_partitions(
    table_name: str, 
    partition_column: str,
    partition_type: str = 'RANGE',
    interval: str = '1 month'
):
    """функций партицирования
    interval: 1 day/ 1 week/ 1 month
    partition_type: LIST/RANGE/HASH
    """
    def _create_partitions(target, connection, **kw):
        connection.execute(text("""
            SELECT create_parent(
                p_parent_table => :table_name,
                p_control => :partition_column,
                p_type => :partition_type,
                p_interval => :interval,
                p_premake => 4,
                p_automatic_maintenance => 'on'
            );
        """).bindparams(
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