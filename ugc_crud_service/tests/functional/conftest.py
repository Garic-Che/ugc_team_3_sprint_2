import pytest
import aiohttp
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient


@pytest_asyncio.fixture
async def ugc_db():
    client = AsyncIOMotorClient("mongodb://admin:password@ugc-crud-db:27017")
    ugc_database = client.ugc
    yield ugc_database
    client.close()


@pytest_asyncio.fixture
async def aiohttp_client():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def fetch(aiohttp_client):
    base_url = "http://ugc_crud_service:8000/api/v1/"
    async def _fetch(url):
        async with aiohttp_client.get(base_url + url) as response:
            return (response.status, await response.json())
    return _fetch
