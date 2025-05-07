from typing import Any
import aiohttp
import asyncio
import pytest
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
import pytest_asyncio
from redis.asyncio import Redis

from tests.functional.settings import (
    TestSettings,
    es_settings,
    redis_settings,
    service_settings,
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="es_client", scope="session")
async def es_client():
    es_client = AsyncElasticsearch(
        hosts=es_settings.get_host(), verify_certs=False
    )
    yield es_client
    try:
        await es_client.close()
    except RuntimeError:
        pass


@pytest_asyncio.fixture(name="redis_client", scope="session")
async def redis_client():
    redis_client = Redis(host=redis_settings.host, port=redis_settings.port)
    yield redis_client
    try:
        await redis_client.aclose()
    except RuntimeError:
        pass


@pytest_asyncio.fixture(name="redis_clear", autouse=True)
async def redis_flushall(redis_client):
    await redis_client.flushall()
    yield


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data(es_client):
    async def inner(
        data: list[dict], test_settings: TestSettings, refresh="wait_for"
    ):
        if await es_client.indices.exists(index=test_settings.es_index):
            await es_client.indices.delete(index=test_settings.es_index)
        await es_client.indices.create(
            index=test_settings.es_index, **test_settings.es_index_mapping
        )

        updated, errors = await async_bulk(
            client=es_client, actions=data, refresh=refresh
        )

        if errors:
            raise Exception("Ошибка записи данных в Elasticsearch")

    return inner


@pytest_asyncio.fixture(name="es_delete_data")
def es_delete_data(es_client):
    async def inner(test_settings: TestSettings):
        if await es_client.indices.exists(index=test_settings.es_index):
            await es_client.indices.delete(index=test_settings.es_index)
        await es_client.indices.create(
            index=test_settings.es_index, **test_settings.es_index_mapping
        )

    return inner


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request():
    async def inner(path: str, parameters: dict[str, Any] = {}):
        session = aiohttp.ClientSession()
        url = service_settings.get_host() + path
        async with session.get(url, params=parameters, timeout=10) as response:
            body = await response.json()
            status = response.status

        await session.close()
        return {"body": body, "status": status}

    return inner


@pytest.fixture(name="es_bulk_query", scope="module")
def es_bulk_query():
    def _es_bulk_query(es_data: list[dict], es_index: str):
        return [
            {"_index": es_index, "_id": str(row["id"]), "_source": row}
            for row in es_data
        ]

    return _es_bulk_query
