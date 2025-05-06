import json


def test_process_click(processor, mock_ch_client):
    # Подготовка тестового сообщения
    message = json.dumps(
        {
            "event_type": "click",
            "user_id": "user1",
            "page_url": "/test",
            "content_type": "film",
            "timestamp": "2023-01-01T12:00:00.000Z",
        }
    )

    # Действие
    processor.process(message)

    # Проверяем, что данные добавились в буфер
    assert len(processor.buffers["clicks"]) == 1
    assert processor.buffers["clicks"][0]["user_id"] == "user1"

    # Принудительно вызываем flush и проверяем execute
    processor._flush("clicks")
    mock_ch_client.execute.assert_called_once()


def test_flush_empty_buffer(processor, mock_ch_client, caplog):
    try:
        processor._flush("clicks")  # Пустой буфер
    except ValueError as e:
        assert "No data to flush" in str(e)
    mock_ch_client.execute.assert_not_called()


def test_invalid_json(processor, caplog):
    processor.process("invalid json")
    assert "Invalid JSON" in caplog.text


def test_missing_field(processor, caplog):
    message = json.dumps({"event_type": "click"})  # Нет user_id
    try:
        processor.process(message)
    except ValueError as e:
        assert "Missing required fields" in str(e)
