from unittest.mock import Mock
import json


def test_kafka_consumption(mock_kafka_consumer, processor):
    # Настраиваем мок
    mock_message = Mock()
    mock_message.value.return_value = json.dumps(
        {
            "event_type": "click",
            "user_id": "user1",
            "page_url": "/test",
            "timestamp": "2023-01-01T12:00:00.000Z",
        }
    ).encode("utf-8")
    mock_kafka_consumer.poll.return_value = mock_message

    # Запускаем обработку
    processor.consume(mock_kafka_consumer)

    # Проверяем
    mock_kafka_consumer.commit.assert_called_once()


def test_kafka_error_handling(mock_kafka_consumer, processor, caplog):
    mock_kafka_consumer.poll.side_effect = Exception("Kafka error")
    processor.consume(mock_kafka_consumer)
    assert "Kafka error" in caplog.text
