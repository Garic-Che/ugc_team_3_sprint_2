from redis.asyncio import Redis

from core import config


async def init_redis() -> Redis:
    redis = Redis(
        host=config.settings.redis_host,
        port=config.settings.redis_port,
    )
    await redis.ping()

    return redis
