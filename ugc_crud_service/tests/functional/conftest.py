import pytest
import aiohttp
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from .settings import settings


@pytest_asyncio.fixture
async def ugc_db():
    client = AsyncIOMotorClient(settings.get_mongodb_connection_string())
    ugc_database = client.ugc
    yield ugc_database
    client.close()


@pytest_asyncio.fixture
async def aiohttp_client():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def fetch(aiohttp_client):
    async def _fetch(url_path):
        headers = {"Authorization": f"Bearer {settings.user_token}"}
        async with aiohttp_client.get(settings.get_base_api_url() + url_path, headers=headers) as response:
            return (response.status, await response.json())
    return _fetch
