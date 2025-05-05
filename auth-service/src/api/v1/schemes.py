from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserAuth(BaseModel):
    login: str | None = None
    password: str | None = None


class Message(BaseModel):
    detail: str = ""


class RefreshToken(BaseModel):
    refresh_token: str = ""


class NewLogin(BaseModel):
    new_login: str


class NewPassword(BaseModel):
    old_password: str = ""
    new_password: str = ""


class Entrance(BaseModel):
    timestamp: str = ""
    user_agent: str = ""


class UpdateAccess(BaseModel):
    access_token: str = ""
    refresh_token: str = ""


class CommonID(BaseModel):
    id: str = ""


class User(BaseModel):
    id: str = ""
    login: Optional[str] = None
    created: datetime


class Role(BaseModel):
    name: str = ""
    privilege_ids: list[str]


class RoleWithID(CommonID):
    name: str = ""
    privilege_ids: list[str]


class RoleResponse(CommonID):
    name: str
    created: datetime
    modified: datetime
    privilege_ids: list[str]
