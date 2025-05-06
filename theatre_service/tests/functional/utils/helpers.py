from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    protocol: str = Field("http://")
    host: str = ...
    port: int = ...

    def get_host(self):
        return f"{self.protocol}{self.host}:{self.port}"


class RedisSettings(CommonSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")


class ElasticsearchSettings(CommonSettings):
    model_config = SettingsConfigDict(env_prefix="es_")


class ServiceSettings(CommonSettings):
    model_config = SettingsConfigDict(env_prefix="THEATRE_SERVICE_")
