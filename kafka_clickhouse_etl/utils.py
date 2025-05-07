import os
import psutil
import logging
import sentry_sdk
from functools import wraps

logger = logging.getLogger("mem-monitor")

# Настройка логирования
logging.basicConfig(
    filename="memory_monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def monitor_memory(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss
        result = func(*args, **kwargs)
        mem_after = process.memory_info().rss

        mem_diff = (mem_after - mem_before) / (1024**2)  # в мегабайтах

        logger.info(
            f"Функция '{func.__name__}' использовала {mem_diff:.2f} МБ памяти"
        )

        if mem_diff > os.environ.get("ETL_MEMORY_THRESHOLD_MB"):
            error_message = (
                f"ПАМЯТЬ: Функция '{func.__name__}' превысила порог {os.environ.get('ETL_MEMORY_THRESHOLD_MB')} МБ: "
                f"{mem_diff:.2f} МБ"
            )
            logger.warning(error_message)
            sentry_sdk.capture_message(error_message, level="warning")

        return result

    return wrapper
