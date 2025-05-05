import time

from redis import Redis
import backoff

from helpers import RedisSettings

@backoff.on_exception(backoff.expo,exception=ValueError,max_time=60)
def is_pinging(client: Redis):
    if not client.ping():
        raise ValueError("Connection failed")

if __name__ == "__main__":
    redis_settings = RedisSettings()
    redis_client = Redis(host=redis_settings.host, port=redis_settings.port)
    is_pinging(redis_client)
