from typing import Any, Optional

import aiohttp
import asyncio
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy import delete
from passlib.context import CryptContext


from tests.functional.utils.helpers import service_settings
from tests.functional.utils.helpers import (
    DBSettings,
    User,
    RefreshToken,
    History,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@pytest_asyncio.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="db_session", scope="session")
async def db_session():
    settings = DBSettings()
    dsn = (
        f"postgresql+asyncpg://{settings.pg_user}:{settings.pg_password}@"
        f"{settings.pg_host}:{settings.pg_port}/{settings.pg_db}"
    )
    engine = create_async_engine(dsn, echo=True, future=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    yield async_session


@pytest_asyncio.fixture(name="clear_db", autouse=True)
async def clear_db(db_session):
    async with db_session() as session:
        await session.execute(delete(History))
        await session.execute(delete(RefreshToken))
        await session.execute(text("DELETE FROM content.user_role"))
        await session.execute(delete(User))
        await session.commit()
    yield


@pytest_asyncio.fixture(name="user_to_db")
def user_to_db(db_session):
    async def inner(user_data):
        async with db_session() as session:
            session.add(user_data)
            await session.commit()
            await session.refresh(user_data)

    return inner


@pytest_asyncio.fixture(name="hash_password")
def hash_password():
    def inner(password: str):
        return pwd_context.hash(password)

    return inner


@pytest_asyncio.fixture(name="make_post_request")
def make_post_request():
    async def inner(
        path: str,
        body: dict[str, Any] = {},
        cookies: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        session = aiohttp.ClientSession()
        url = service_settings.get_host() + path

        # Подготовка параметров запроса
        request_params = {
            "json": body,
            "cookies": cookies or {},
            "headers": headers or {},
        }

        print(f"Making POST request to {url} with params: {request_params}")

        async with session.post(url, **request_params) as response:
            try:
                response_body = await response.json()
            except:
                response_body = await response.text()

            status = response.status
            response_cookies = response.cookies

            print(
                f"Response: status={status}, body={response_body}, cookies={response_cookies}"
            )

        await session.close()
        return {
            "body": response_body,
            "status": status,
            "cookies": response_cookies,
        }

    return inner


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request():
    async def inner(
        path: str,
        params: dict[str, Any] = {},
        cookies: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        session = aiohttp.ClientSession()
        url = service_settings.get_host() + path

        # Подготовка параметров запроса
        request_params = {
            "params": params,
            "cookies": cookies or {},
            "headers": headers or {},
        }

        print(f"Making GET request to {url} with params: {request_params}")

        async with session.get(url, **request_params) as response:
            try:
                response_body = await response.json()
            except:
                response_body = await response.text()

            status = response.status
            response_cookies = response.cookies

            print(
                f"Response: status={status}, body={response_body}, cookies={response_cookies}"
            )

        await session.close()
        return {
            "body": response_body,
            "status": status,
            "cookies": response_cookies,
        }

    return inner


@pytest_asyncio.fixture(name="make_put_request")
def make_put_request():
    async def inner(
        path: str,
        body: dict[str, Any] = {},
        cookies: Optional[dict[str, str]] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        session = aiohttp.ClientSession()
        url = service_settings.get_host() + path

        # Подготовка параметров запроса
        request_params = {
            "json": body,
            "cookies": cookies or {},
            "headers": headers or {},
        }

        print(f"Making PUT request to {url} with params: {request_params}")

        async with session.put(url, **request_params) as response:
            try:
                response_body = await response.json()
            except:
                response_body = await response.text()

            status = response.status
            response_cookies = response.cookies

            print(
                f"Response: status={status}, body={response_body}, cookies={response_cookies}"
            )

        await session.close()
        return {
            "body": response_body,
            "status": status,
            "cookies": response_cookies,
        }

    return inner
