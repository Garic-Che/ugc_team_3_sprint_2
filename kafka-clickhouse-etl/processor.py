from clickhouse_driver import Client
from datetime import datetime
from uuid import uuid4
import logging
from typing import Any

from utils import monitor_memory

logger = logging.getLogger(__name__)

class EventProcessor:
    def __init__(self, ch_client: Client):
        self.ch_client = ch_client
        self.buffers = {
            "clicks": [],
            "visits": [],
            "resolution_changes": [],
            "completed_viewings": [],
            "filter_applications": []
        }

    @monitor_memory
    def process(self, message: str):
        """Основной метод обработки сообщения из Kafka"""
        try:
            event = json.loads(message)
            event_type = event.get("event_type")

            if not event_type:
                raise ValueError("Missing 'event_type' in message")

            processor_map = {
                "click": self._process_click,
                "page_visit": self._process_visit,
                "resolution_change": self._process_resolution_change,
                "completed_viewing": self._process_completed_viewing,
                "filter_application": self._process_filter_application
            }

            if event_type not in processor_map:
                raise ValueError(f"Unknown event type: {event_type}")

            processor_map[event_type](event)

            # Проверка на заполнение буферов
            for table, buffer in self.buffers.items():
                if len(buffer) >= 1000:  # Размер пачки
                    self._flush(table)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}\nMessage: {message[:200]}...")
        except Exception as e:
            logger.error(f"Failed to process event: {str(e)}")
            raise

    def _process_click(self, event: dict[str, Any]):
        """Обработка события клика"""
        required_fields = ["user_id", "page_url", "content_type", "timestamp"]
        self._validate_event(event, required_fields)

        self.buffers["clicks"].append({
            "id": str(uuid4()),
            "event_time": datetime.strptime(event["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            "user_id": event["user_id"],
            "page_url": event["page_url"],
            "content_type": event["content_type"]
        })

    def _process_visit(self, event: dict[str, Any]):
        """Обработка события посещения страницы"""
        required_fields = ["user_id", "page_url", "page_type", "started_at", "finished_at"]
        self._validate_event(event, required_fields)

        self.buffers["visits"].append({
            "id": str(uuid4()),
            "user_id": event["user_id"],
            "page_url": event["page_url"],
            "page_type": event["page_type"],
            "started_at": datetime.strptime(event["started_at"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            "finished_at": datetime.strptime(event["finished_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        })

    def _process_resolution_change(self, event: dict[str, Any]):
        """Обработка изменения разрешения видео"""
        required_fields = ["user_id", "video_id", "target_resolution", "origin_resolution", "timestamp"]
        self._validate_event(event, required_fields)

        self.buffers["resolution_changes"].append({
            "id": str(uuid4()),
            "event_time": datetime.strptime(event["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            "user_id": event["user_id"],
            "video_id": event["video_id"],
            "target_resolution": event["target_resolution"],
            "origin_resolution": event["origin_resolution"]
        })

    def _process_completed_viewing(self, event: dict[str, Any]):
        """Обработка завершения просмотра"""
        required_fields = ["user_id", "video_id", "timestamp"]
        self._validate_event(event, required_fields)

        self.buffers["completed_viewings"].append({
            "id": str(uuid4()),
            "event_time": datetime.strptime(event["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            "user_id": event["user_id"],
            "video_id": event["video_id"]
        })

    def _process_filter_application(self, event: dict[str, Any]):
        """Обработка применения фильтра"""
        required_fields = ["user_id", "filter_type", "filter_value", "timestamp"]
        self._validate_event(event, required_fields)

        self.buffers["filter_applications"].append({
            "id": str(uuid4()),
            "event_time": datetime.strptime(event["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"),
            "user_id": event["user_id"],
            "filter_type": event["filter_type"],
            "filter_value": event["filter_value"]
        })

    def _validate_event(self, event: dict[str, Any], required_fields: list[str]):
        """Валидация обязательных полей события"""
        missing_fields = [field for field in required_fields if field not in event]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    def _flush(self, table: str):
        """Отправка накопленных данных в ClickHouse"""
        if not self.buffers[table]:
            return

        try:
            match table:
                case "clicks":
                    self.ch_client.execute(
                        "INSERT INTO shard.clicks (id, event_time, user_id, page_url, content_type) VALUES",
                        self.buffers[table]
                )
                case "visits":
                    self.ch_client.execute(
                        "INSERT INTO shard.visits (id, user_id, page_url, page_type, started_at, finished_at) VALUES",
                        self.buffers[table]
                    )
                case "resolution_changes":
                    self.ch_client.execute(
                        "INSERT INTO shard.resolution_changes (id, event_time, user_id, video_id, target_resolution, origin_resolution) VALUES",
                        self.buffers[table]
                    )
                case "completed_viewings":
                    self.ch_client.execute(
                        "INSERT INTO shard.completed_viewings (id, event_time, user_id, video_id) VALUES",
                        self.buffers[table]
                    )
                case "filter_applications":
                    self.ch_client.execute(
                        "INSERT INTO shard.filter_applications (id, event_time, user_id, filter_type, filter_value) VALUES",
                        self.buffers[table]
                    )

            logger.info(f"Inserted {len(self.buffers[table])} rows to {table}")
            self.buffers[table].clear()

        except Exception as e:
            logger.error(f"Failed to insert to {table}: {str(e)}")
            raise

    def flush_all(self):
        """Принудительная отправка всех буферов"""
        for table in self.buffers.keys():
            self._flush(table)