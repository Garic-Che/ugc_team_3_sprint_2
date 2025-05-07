import os
from logging import config as logging_config
from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        extra="allow"
    )

    # Название проекта. Используется в Swagger-документации
    auth_project_name: str = "Auth-API"
    auth_project_description: str = "API для авторизации и аутентификации"
    auth_project_version: str = "1.0.0"

    # Настройки Redis
    token_redis_host: str = Field(..., alias="TOKEN_REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    # Настройки Postgres
    pg_host: str = Field(..., alias="AUTH_DB_HOST")
    pg_port: int = Field(..., alias="AUTH_DB_PORT")
    pg_user: str = Field(..., alias="AUTH_DB_USER")
    pg_password: str = Field(..., alias="AUTH_DB_PASSWORD")
    pg_db: str = Field(..., alias="AUTH_DB_DATABASE")

    # Другие важные константы
    auth_secret_key: str = Field(..., alias="AUTH_SECRET_KEY")
    access_token_expires_in: int = Field(..., alias="ACCESS_TOKEN_EXPIRES_IN")
    refresh_token_expires_in: int = Field(..., alias="REFRESH_TOKEN_EXPIRES_IN")
    algorithm: str = "HS256"

    # Настройки Google OAuth
    google_client_id: str = Field(..., alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., alias="GOOGLE_CLIENT_SECRET")

    # VK OAuth settings (not showing off, just lacking Russian on my VM =))
    vk_client_id: str = Field(..., alias="VK_CLIENT_ID")
    vk_client_secret: str = Field(..., alias="VK_CLIENT_SECRET")

    enable_tracing: bool = Field(True, env="ENABLE_TRACING")
    jaeger_host: str = Field("jaeger", env="JAEGER_HOST")
    jaeger_port: int = Field(6831, env="JAEGER_PORT")

    # Redis instance backing fast api rate limiter
    limiter_redis_host: str = Field('limiter-db', alias='LIMITER_REDIS_HOST')
    limiter_redis_port: int = Field(6379, alias='LIMITER_REDIS_PORT')


# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

settings = Settings()
