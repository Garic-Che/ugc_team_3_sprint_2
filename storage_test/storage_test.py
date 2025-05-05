import datetime
import logging
import random
import time
import threading
import queue
from contextlib import contextmanager
from functools import wraps
from typing import List, Tuple
from clickhouse_driver import Client as ClickhouseClient
from vertica_python import connect as VerticaConnect
from queue import Queue

import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Конфигурация
CLICKHOUSE_CONFIG = {
    "host": os.getenv("CLICKHOUSE_HOST"),
    "port": int(os.getenv("CLICKHOUSE_PORT")),
    "user": os.getenv("CLICKHOUSE_USER"),
    "password": os.getenv("CLICKHOUSE_PASSWORD"),
    "database": os.getenv("CLICKHOUSE_DATABASE"),
}

VERTICA_CONFIG = {
    "host": os.getenv("VERTICA_HOST"),
    "port": int(os.getenv("VERTICA_PORT")),  # порт должен быть int
    "user": os.getenv("VERTICA_DB_USER"),
    "password": os.getenv("VERTICA_DB_PASSWORD"),
    "database": os.getenv("VERTICA_DB_NAME"),
    "tlsmode": "disable",
}

BATCH_SIZE = 500
COUNT_ITERATION = 100
DURATION = 30
TABLE = "events"
TEST_QUERY = """
            SELECT event_type, count(*) 
            FROM events
            WHERE event_type = 'done'
            GROUP BY event_type
        """
QUERY_INSERT_VERTICE = f"""
            INSERT INTO {TABLE} 
            (event_date, event_time, user_id, event_type, value)
            VALUES (%s, %s, %s, %s, %s)
        """


def generate_batch(batch_size=BATCH_SIZE):
    """Генерация данных"""
    logger.debug(f"Генерация данных, batch = {batch_size}")
    base_time = datetime.datetime.now()
    return tuple(
        (
            (base_time - datetime.timedelta(seconds=random.randint(0, 2592000))).date(),
            base_time - datetime.timedelta(seconds=random.randint(0, 2592000)),
            random.randint(1, 100000),
            random.choice(["test", "batch", "done", "gen"]),
            round(random.uniform(0, 1000), 2),
        )
        for _ in range(batch_size)
    )


class ClickHouseManager:
    def __init__(self, config: dict):
        self.config = config
        self._connection = None

    def _connect(self):
        return ClickhouseClient(**self.config)

    @contextmanager
    def connection(self):
        """Подключение к базе"""
        conn = None
        try:
            conn = self._connect()
            yield conn
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
        finally:
            if conn:
                conn.disconnect()

    @staticmethod
    def speed_time(func):
        """Замер времени выполнения функции"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            stop = time.perf_counter() - start
            logger.debug(f"{func.__name__} выполнен за {stop:.4f}s")
            return result

        return wrapper

    def execute_insert(self, conn, data, table: str = "events"):
        """Выполнение вставки"""
        conn.execute(f"INSERT INTO {table} VALUES", data)
        logger.debug(f"Вставка в {table}: {len(data)}")

    @speed_time
    def insert_data(self, data: List[Tuple], table: str = "events") -> None:
        """Вставка данных"""
        if not data:
            logger.warning(f"Нет данных для {table}")
            return

        try:
            with self.connection() as conn:
                self.execute_insert(conn, data)
        except Exception as e:
            logger.error(f"Ошибка вставки: {e}")
            raise

    @speed_time
    def execute_query(self, conn, query: str, params: dict = None) -> List[Tuple]:
        """Выполнение запроса"""
        try:
            return conn.execute(query, params)
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            raise

    @speed_time
    def load_test(self, count_iterations: int, data_generator) -> dict:
        """Тест загрузки"""
        logger.debug(f"Загрузка записей ...")
        results = {"total_time": 0, "avg_time": 0, "errors": 0, "success": 0}

        for i in range(count_iterations):
            try:
                start = time.perf_counter()
                self.insert_data(table="events", data=data_generator())
                results["total_time"] += time.perf_counter() - start
                results["success"] += 1
            except Exception as e:
                results["errors"] += 1
                logger.debug(f"Ошибка теста записи: {e}")

        results["avg_time"] = (
            results["total_time"] / results["success"] if results["success"] else 0
        )

        return results


class VerticaManager(ClickHouseManager):
    def __init__(self, config: dict):
        super().__init__(config)
        self._connection = None

    def _connect(self):
        return VerticaConnect(**self.config)

    @contextmanager
    def connection(self):
        """Подключение к базе"""
        conn = None
        try:
            conn = self._connect()
            yield conn
        except Exception as e:
            logger.error(f"Connection error: {e}")
            conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_insert(self, conn, data, table: str = "events"):
        """Выполнение вставки"""
        cursor = conn.cursor()
        cursor.executemany(QUERY_INSERT_VERTICE, data)
        conn.commit()

    def insert_data(self, table: str, data: List[Tuple]) -> None:
        """Вставка данных"""
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(QUERY_INSERT_VERTICE, data)
                conn.commit()
                logger.debug(f"Вставка в {table}: {len(data)}")
        except Exception as e:
            logger.error(f"Ошибка вставки: {e}")
            raise

    def execute_query(self, conn, query: str, params: dict = None) -> List[Tuple]:
        """Выполнение запроса"""
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            raise


class RealtimeTester:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.query_queue = Queue()
        self.is_running = True
        self.stats = {"inserted": 0, "errors": 0, "query_times": []}

    @contextmanager
    def _speed_time(self, operation: str):
        """Змер времени через with"""
        try:
            start = time.perf_counter()
            yield
        finally:
            stop = time.perf_counter() - start
            self.stats["query_times"].append(stop)
            logger.debug(f"{operation} выполнена за {stop:.4f}s")

    def _batch_insert(self, data: Tuple):
        """Вставка пачкой"""
        try:
            with self.db_manager.connection() as conn:
                with self._speed_time(operation="Вставка"):
                    self.db_manager.execute_insert(conn, data)
                    self.stats["inserted"] += len(data)

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Ошибка при вставке: {e}", exc_info=True)

    def _background_insert(self):
        """Фоновая вставка"""
        while self.is_running:
            data = generate_batch(BATCH_SIZE)
            self._batch_insert(data)
            time.sleep(1)  # Регулируем нагрузку слипом

    def _query_worker(self):
        """Обработчик запросов"""
        while self.is_running or not self.query_queue.empty():
            try:
                self.query_queue.get(block=True, timeout=0.5)  # без таймаута ругался ch

                with self.db_manager.connection() as conn:
                    with self._speed_time(operation="Запрос"):
                        self.db_manager.execute_query(conn, TEST_QUERY)
                        self.query_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Ошибка запроса: {e}")
                self.query_queue.task_done()

    def test_under_load(self, duration_sec=60, workers: int = 2):
        """Тест под нагрузкой"""
        insert_thread = threading.Thread(target=self._background_insert)
        insert_thread.start()

        # запускаем воркеры
        worker_threads = []
        for _ in range(workers):
            t = threading.Thread(target=self._query_worker)
            t.start()
            worker_threads.append(t)

        # заполняем очередь
        for _ in range(workers * 4):
            self.query_queue.put(TEST_QUERY)

        time.sleep(duration_sec)

        # остановка теста и ожидание воркеров
        self.is_running = False
        for t in worker_threads:
            t.join()


        # завершение вставки и задач в очереди
        insert_thread.join()
        self.query_queue.join()

        # результат по времени
        total_queries = len(self.stats["query_times"])
        avg_query_time = (
            sum(self.stats["query_times"]) / total_queries if total_queries else 0
        )

        logger.info(
            f"""
            Результат:
            - Вставлено данных: {self.stats['inserted']}
            - Среднее время запроса: {avg_query_time:.4f}s
            - Всего запросов: {total_queries}
            - Ошибки: {self.stats['errors']}
        """
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    ch = ClickHouseManager(CLICKHOUSE_CONFIG)
    try:
        with ch.connection() as conn:
            logger.info("Подключение к ClickHouse")

        # тест загрузки данных ClickHouse
        results = ch.load_test(COUNT_ITERATION, generate_batch)
        logger.info(
            f"Общее время: {results['total_time']:.2f}s, Среднее время: {results['avg_time']:.2f}s"
        )

    except Exception as e:
        logger.error(f"Ошибка подключения к ClickHouse: {e}")

    # тест под нагрузкой ClickHouse
    logger.info("Запуск теста под нагрузкой для ClickHouse")
    tester = RealtimeTester(db_manager=ch)
    tester.test_under_load(duration_sec=DURATION)


    vrt = VerticaManager(VERTICA_CONFIG)
    try:
        with vrt.connection() as conn:
            logger.info("Подключение к Vertica")

        # тест загрузки данных Vertica
        results = vrt.load_test(COUNT_ITERATION, generate_batch)
        logger.info(
            f"Общее время: {results['total_time']:.2f}s, Среднее время: {results['avg_time']:.2f}s"
        )
    except Exception as e:
        logger.error(f"Ошибка подключения к Vertica: {e}")

    # тест под нагрузкой Vertica
    logger.info("Запуск теста под нагрузкой для Vertica")
    tester = RealtimeTester(db_manager=vrt)
    tester.test_under_load(duration_sec=DURATION)
