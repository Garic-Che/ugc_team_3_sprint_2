from datetime import datetime, timezone

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="allow")

    mongo_host: str = Field(..., alias="MONGO_DB_HOST")
    mongo_port: int = Field(..., alias="MONGO_DB_PORT")
    mongo_root_username: str = Field(..., alias="MONGO_ROOT_USERNAME")
    mongo_root_password: str = Field(..., alias="MONGO_ROOT_PASSWORD")
    mongo_db_name: str = Field(..., alias="MONGO_DB_NAME")

    jwt_secret_key: str = Field(..., alias="AUTH_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")

    def get_mongodb_connection_string(self):
        username = self.mongo_root_username
        password = self.mongo_root_password
        host = self.mongo_host
        port = self.mongo_port
        return f"mongodb://{username}:{password}@{host}:{port}"
    
    def get_timezone_aware_now(self):
        return datetime.now(timezone.utc)
    

settings = Settings()
