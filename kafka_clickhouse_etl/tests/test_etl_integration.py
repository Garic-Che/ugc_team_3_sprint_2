# test_etl_integration.py
import json
import time
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from confluent_kafka import Producer
from clickhouse_driver import Client as ClickHouseClient
from kafka_clickhouse_etl.processor import EventProcessor

# Конфигурация тестов
TEST_TOPIC = "event"
TEST_KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9094",
    "auto.offset.reset": "earliest",
    "group.id": "test-etl-group",
    "enable.auto.commit": False
}
TEST_CLICKHOUSE_CONFIG = {
    "host": "localhost",
    "port": 9000,
    "user": "default",
    "password": "",
    "database": "shard"
}

@pytest.fixture(scope="module")
def kafka_producer():
    producer = Producer({"bootstrap.servers": TEST_KAFKA_CONFIG["bootstrap.servers"]})
    yield producer
    producer.flush()

@pytest.fixture(scope="module")
def message_processor(clickhouse_client):
    yield EventProcessor(clickhouse_client)

@pytest.fixture(scope="module")
def clickhouse_client():
    client = ClickHouseClient(**TEST_CLICKHOUSE_CONFIG)
    yield client
    client.disconnect()

@pytest.fixture(scope="function")
def clean_clickhouse_tables(clickhouse_client):
    """Очистка тестовых таблиц перед каждым тестом"""
    tables = [
        "clicks",
        "visits",
        "resolution_changes",
        "completed_viewings",
        "filter_applications"
    ]
    for table in tables:
        clickhouse_client.execute(f"TRUNCATE TABLE IF EXISTS shard.{table}")

def generate_test_event(event_type, **kwargs):
    """Генератор тестовых событий"""
    base_event = {
        "event_type": event_type,
        "user_id": str(uuid4()),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }

    if event_type == "click":
        base_event.update({
            "page_url": "http://test.com/movie123",
            "content_type": "movie"
        })
    elif event_type == "page_visit":
        base_event.update({
            "page_url": "http://test.com/movies",
            "page_type": "catalog",
            "started_at": (datetime.utcnow() - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "finished_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        })
    elif event_type == "resolution_change":
        base_event.update({
            "video_id": str(uuid4()),
            "target_resolution": "1080p",
            "origin_resolution": "720p"
        })
    elif event_type == "completed_viewing":
        base_event.update({
            "video_id": str(uuid4())
        })
    elif event_type == "filter_application":
        base_event.update({
            "filter_type": "genre",
            "filter_value": "comedy"
        })

    base_event.update(kwargs)
    return base_event

def test_click_event_processing(message_processor, clickhouse_client, clean_clickhouse_tables):
    """Тестирование обработки события клика"""
    # 1. Генерация тестового события
    test_event = generate_test_event("click")
    message = json.dumps(test_event)

    # 2. Отправка в Kafka
    message_processor.process(message)
    message_processor.flush_all()

    # 3. Ожидание обработки (можно заменить на более надежный механизм)
    time.sleep(5)

    # 4. Проверка в ClickHouse
    result = clickhouse_client.execute(
        "SELECT user_id, page_url, content_type FROM shard.clicks LIMIT 1"
    )

    assert len(result) == 1
    assert result[0][0] == test_event["user_id"]
    assert result[0][1] == test_event["page_url"]
    assert result[0][2] == test_event["content_type"]

def test_visit_event_processing(kafka_producer, clickhouse_client, clean_clickhouse_tables):
    """Тестирование обработки события посещения"""
    test_event = generate_test_event("page_visit")
    message = json.dumps(test_event)

    kafka_producer.produce(TEST_TOPIC, value=message)
    kafka_producer.flush()
    time.sleep(5)

    result = clickhouse_client.execute(
        "SELECT user_id, page_url, page_type FROM shard.visits LIMIT 1"
    )

    assert len(result) == 1
    assert result[0][0] == test_event["user_id"]
    assert result[0][1] == test_event["page_url"]
    assert result[0][2] == test_event["page_type"]

def test_batch_processing(kafka_producer, clickhouse_client, clean_clickhouse_tables):
    """Тестирование пакетной обработки событий"""
    # Генерация 5 событий каждого типа
    for event_type in ["click", "page_visit", "resolution_change", "completed_viewing", "filter_application"]:
        for _ in range(5):
            test_event = generate_test_event(event_type)
            kafka_producer.produce(TEST_TOPIC, value=json.dumps(test_event))

    kafka_producer.flush()
    time.sleep(10)  # Даем больше времени на обработку батча

    # Проверяем количество записей в каждой таблице
    tables = [
        "clicks",
        "visits",
        "resolution_changes",
        "completed_viewings",
        "filter_applications"
    ]

    for table in tables:
        count = clickhouse_client.execute(f"SELECT count() FROM shard.{table}")[0][0]
        assert count == 5, f"Expected 5 records in {table}, got {count}"

def test_invalid_event_handling(kafka_producer, clickhouse_client, clean_clickhouse_tables):
    """Тестирование обработки некорректных событий"""
    # 1. Невалидный JSON
    kafka_producer.produce(TEST_TOPIC, value="invalid json")

    # 2. Событие без типа
    kafka_producer.produce(TEST_TOPIC, value=json.dumps({"user_id": "123"}))

    # 3. Неизвестный тип события
    kafka_producer.produce(TEST_TOPIC, value=json.dumps({"event_type": "unknown"}))

    kafka_producer.flush()
    time.sleep(5)

    # Проверяем, что в таблицы не попало лишних данных
    tables = [
        "clicks",
        "visits",
        "resolution_changes",
        "completed_viewings",
        "filter_applications"
    ]

    for table in tables:
        count = clickhouse_client.execute(f"SELECT count() FROM shard.{table}")[0][0]
        assert count == 0, f"Table {table} should be empty after invalid events"

def test_required_fields_validation(kafka_producer, clickhouse_client, clean_clickhouse_tables):
    """Тестирование валидации обязательных полей"""
    # Событие клика без обязательного поля content_type
    test_event = generate_test_event("click")
    del test_event["content_type"]

    kafka_producer.produce(TEST_TOPIC, value=json.dumps(test_event))
    kafka_producer.flush()
    time.sleep(5)

    count = clickhouse_client.execute("SELECT count() FROM shard.clicks")[0][0]
    assert count == 0, "Event with missing required field should not be processed"