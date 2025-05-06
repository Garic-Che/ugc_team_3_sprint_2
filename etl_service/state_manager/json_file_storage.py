import json
import os
from json import JSONDecodeError
from logging import Logger
from typing import Any

from filelock import FileLock
from state_manager.base_storage import BaseStorage


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


class JsonFileStorage(BaseStorage):
    """Реализация хранилища, использующего локальный файл.

    Формат хранения: JSON
    """

    _file_path: str
    _logger: Logger

    def __init__(self, logger: Logger, file_path: str | None = './storage/state_storage.json') -> None:
        if file_path is None:
            raise ValueError("file_path can't be None")

        self._file_path = file_path

        self._logger = logger
        create_directory('./storage')

    def save_state(self, state: dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""
        lock = FileLock(f'{self._file_path}.lock')
        with lock:
            with open(file=self._file_path, mode='w', encoding='utf-8') as json_storage:
                json.dump(state, json_storage)

    def retrieve_state(self) -> dict[str, Any]:
        """Получить состояние из хранилища."""
        try:
            lock = FileLock(f'{self._file_path}.lock')
            with lock:
                with open(file=self._file_path, mode='r', encoding='utf-8') as json_storage:
                    return json.load(json_storage)
        except (FileNotFoundError, JSONDecodeError):
            self._logger.warning('No state file provided. Continue with default file')
            return {}
        except Exception as e:
            self._logger.exception(e)
            raise e
