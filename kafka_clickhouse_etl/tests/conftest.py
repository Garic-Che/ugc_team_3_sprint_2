import pytest
from unittest.mock import Mock
from clickhouse_driver import Client
from confluent_kafka import Consumer

from kafka_clickhouse_etl.processor import EventProcessor


@pytest.fixture
def mock_ch_client():
    """Фиктивный клиент ClickHouse"""
    client = Mock(spec=Client)
    client.execute.return_value = None
    return client


@pytest.fixture
def mock_kafka_consumer():
    """Фиктивный Kafka Consumer"""
    consumer = Mock(spec=Consumer)
    consumer.poll.return_value = None
    return consumer


@pytest.fixture
def processor(mock_ch_client):
    """Инициализированный процессор с моком ClickHouse"""
    return EventProcessor(mock_ch_client)
