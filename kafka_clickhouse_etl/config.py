from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Kafka configuration
    kafka_bootstrap_server: str
    kafka_group_id: str = "ugc-etl-group"
    kafka_auto_offset_reset: str = "earliest"
    kafka_enable_auto_commit: bool = False

    # ClickHouse configuration
    clickhouse_nodes: str
    clickhouse_port: int = 9000
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "shard"

    # ETL configuration
    topic: str = "event"
    batch_size: int = 1000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def kafka_config(self) -> dict:
        return {
            "bootstrap.servers": self.kafka_bootstrap_server,
            "auto.offset.reset": self.kafka_auto_offset_reset,
            "group.id": self.kafka_group_id,
            "enable.auto.commit": self.kafka_enable_auto_commit,
        }

    @property
    def clickhouse_config(self) -> dict:
        nodes = self.clickhouse_nodes.split(",")
        return {
            "host": nodes[0],
            "alt_hosts": ",".join(nodes[1:]) if len(nodes) > 1 else "",
            "port": self.clickhouse_port,
            "user": self.clickhouse_user,
            "password": self.clickhouse_password,
            "database": self.clickhouse_database,
        }


settings = Settings()
