import logging
import logging.handlers
from pathlib import Path


def setup_logging():
    # Общий формат логов
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Основной логгер для консоли (все модули)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Применяем ко всем логгерам
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Отдельный логгер для конкретного скрипта
    special_logger = logging.getLogger("mem_monitor")
    special_logger.propagate = (
        False  # Отключаем дублирование в корневой логгер
    )

    # Файловый обработчик только для special_module
    log_file = Path("logs/memory_monitor.log")
    log_file.parent.mkdir(exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    special_logger.addHandler(file_handler)
