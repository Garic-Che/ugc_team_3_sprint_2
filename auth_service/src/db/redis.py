from redis.asyncio import Redis

from core.config import settings


async def init_redis() -> Redis:
    redis = Redis(
        host=settings.token_redis_host,
        port=settings.redis_port,
    )
    await redis.ping()
    return redis


async def init_limiter_redis() -> Redis:
    redis = Redis(
        host=settings.limiter_redis_host,
        port=settings.redis_port,
        encoding="utf-8",
        decode_responses=True
    )
    await redis.ping()
    return redis
