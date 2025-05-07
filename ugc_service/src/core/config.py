import os
from logging import config as logging_config
from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )

    # Безопасность
    # Секретный ключ (должен быть одинаковый для frontend и backend)
    ugc_api_secret_key: str = Field(..., alias="UGC_API_SECRET_KEY")

    # Настройки Kafka
    kafka_bootstrap_servers: str = Field(..., alias="KAFKA_BOOTSTRAP_SERVER")
    kafka_topic_name: str = Field("event", alias="KAFKA_TOPIC_NAME")

    # Настройки Redis для rate limiting
    ugc_limiter_redis_url: str = "redis://ugc-limiter-db:6379"

    # Настройки Sentry
    sentry_dsn: str = Field(..., alias="SENTRY_DSN_UGC")


# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

settings = Settings()
