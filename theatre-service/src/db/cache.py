import logging
from typing import Optional, Any, Protocol

import redis.exceptions
from fastapi import Request, Depends
from redis.asyncio import Redis
from redis.exceptions import ConnectionError
import backoff

NO_CACHE_AFTER_PAGE_NUMBER = 10


class CacheStorage(Protocol):
    async def get(self, key: str) -> Optional[Any]:
        pass

    async def set(self, key: str, value: Any, expire: int) -> None:
        pass


class RedisCacheStorage(CacheStorage):
    def __init__(self, redis: Redis):
        self.redis = redis

    @backoff.on_exception(backoff.expo, exception=ConnectionError, max_time=60)
    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        logging.info(f"Get from cache: {key}")
        return data

    @backoff.on_exception(backoff.expo, exception=ConnectionError, max_time=60)
    async def set(self, key: str, value: Any, expire: int) -> None:
        await self.redis.set(key, value, ex=expire)
        logging.info(f"Put to cache: {key}")


class CacheRules:
    def need_cache(self, page_number: Optional[int] = None) -> bool:
        return (
            page_number <= NO_CACHE_AFTER_PAGE_NUMBER if page_number else True
        )


async def get_redis(request: Request) -> Redis:
    return request.app.state.cache_engine


def get_cache_storage(redis: Redis = Depends(get_redis)) -> CacheStorage:
    return RedisCacheStorage(redis)
