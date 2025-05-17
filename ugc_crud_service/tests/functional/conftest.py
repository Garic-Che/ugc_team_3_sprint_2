import pytest
import aiohttp
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from .testdata.like import likes
from .testdata.comment import comments
from .testdata.bookmark import bookmarks


@pytest_asyncio.fixture
async def ugc_db():
    client = AsyncIOMotorClient("mongodb://admin:password@ugc-crud-db:27017")
    ugc_database = client.ugc

    await ugc_database.Like.insert_many(likes)
    await ugc_database.Comment.insert_many(comments)
    await ugc_database.Bookmark.insert_many(bookmarks)

    yield ugc_database

    client.close()


@pytest_asyncio.fixture
async def aiohttp_client():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def fetch(aiohttp_client):
    async def _fetch(url):
        async with aiohttp_client.get(url) as response:
            return await response.json()
    return _fetch
