import os
from logging import config as logging_config
from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    # Название проекта. Используется в Swagger-документации
    project_name: str = "Read-only API для онлайн-кинотеатра"
    project_description: str = (
        "Информация о фильмах, жанрах и людях, "
        "участвовавших в создании произведения"
    )
    project_version: str = "1.0.0"

    # Настройки Redis
    redis_host: str = Field(..., alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    # Настройки Elasticsearch
    es_schema: str = "http://"
    es_host: str = Field(..., alias="ES_HOST")
    es_port: int = Field(9200, alias="ES_PORT")

    # auth-server
    auth_service_schema: str = "http://"
    auth_service_host: str = Field("auth_service", alias="AUTH_SERVICE_HOST")
    auth_service_port: int = Field(8000, alias="AUTH_SERVICE_PORT")
    jwt_secret_key: str = Field(..., alias="AUTH_SECRET_KEY")
    jwt_algorithm: str = "HS256"

    # Sentry configuration
    sentry_dsn_theatre: str = Field(..., alias="SENTRY_DSN_THEATRE")


# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

settings = Settings()
