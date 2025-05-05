import json
import logging
from typing import Any

from kafka import KafkaProducer
from kafka.errors import KafkaError

from core.config import settings

# Инициализация продюссера Kafka
producer = KafkaProducer(
    bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    retries=5,
)


def send_to_broker(
    topic: Any = settings.kafka_topic_name,
    value: Any | None = None,
    key: Any | None = None,
):
    try:
        producer.send(
            topic=topic,
            value=value,
            key=key,
        )
        producer.flush()
    except KafkaError as e:
        logging.error(f"Failed to send message to Kafka: {str(e)}")
        raise
