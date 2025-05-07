from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional


# Базовые модели для общих полей
class UserBase(BaseModel):
    login: str
    password: str


class RoleBase(BaseModel):
    name: str


class PrivilegeBase(BaseModel):
    name: str


class RefreshTokenBase(BaseModel):
    token: str
    expired: Optional[datetime] = None


class HistoryBase(BaseModel):
    user_agent: str
    entered: datetime


# Модели для создания (без ID и временных меток)
class UserCreate(UserBase):
    pass


class RoleCreate(RoleBase):
    pass


class PrivilegeCreate(PrivilegeBase):
    pass


class RefreshTokenCreate(RefreshTokenBase):
    user_id: UUID4


class HistoryCreate(HistoryBase):
    user_id: UUID4


# Модели для ответов (с ID и временными метками)
class UserResponse(UserBase):
    id: UUID4
    created: datetime
    modified: datetime
    roles: list["RoleResponse"] = []

    class Config:
        orm_mode = True  # Включение поддержки ORM


class RoleResponse(RoleBase):
    id: UUID4
    created: datetime
    modified: datetime
    privileges: list["PrivilegeResponse"] = []

    class Config:
        orm_mode = True


class PrivilegeResponse(PrivilegeBase):
    id: UUID4
    created: datetime
    modified: datetime

    class Config:
        orm_mode = True


class RefreshTokenResponse(RefreshTokenBase):
    id: UUID4
    user_id: UUID4
    created: datetime

    class Config:
        orm_mode = True


class HistoryResponse(HistoryBase):
    id: UUID4
    user_id: UUID4

    class Config:
        orm_mode = True


# Обновление моделей для рекурсивных ссылок
UserResponse.model_rebuild()
RoleResponse.model_rebuild()
