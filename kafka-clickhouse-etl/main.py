import logging
import signal
import sys

from clickhouse_driver import Client

from config import settings
from processor import EventProcessor
from consumer import KafkaConsumer
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def shutdown_handler(signum, frame):
    logger.info("Shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Обработка SIGTERM для graceful shutdown
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    logger.info("Starting ETL service...")

    try:
        # Подключение к ClickHouse
        logger.info(f"Connecting to ClickHouse server by {settings.clickhouse_config}")
        ch_client = Client(**settings.clickhouse_config)
        ch_client.execute("SELECT 1")  # Проверка подключения
        logger.info("Connected to ClickHouse")

        # Инициализация процессора
        processor = EventProcessor(ch_client)

        # Запуск Kafka Consumer
        consumer = KafkaConsumer(settings.kafka_config)
        logger.info(f"Subscribed to topic: {settings.topic}")
        consumer.consume(settings.topic, processor.process)

    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)