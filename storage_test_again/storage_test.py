import logging
import os
import random
import threading
import time
import queue
from dotenv import load_dotenv
from contextlib import contextmanager
from postgres_manager import PostgresManager
from pymongo import MongoClient
from mongo_manager import MongoManager
from queue import Queue

logger = logging.getLogger(__name__)

load_dotenv()

# Конфигурация
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB"),
}

MONGO_CONFIG = {
    "host": os.getenv("MONGO_HOST"),
    "port": int(os.getenv("MONGO_PORT")),
    "user": os.getenv("MONGO_INITDB_ROOT_USERNAME"),
    "password": os.getenv("MONGO_INITDB_ROOT_PASSWORD"),
    "database": os.getenv("MONGO_DATABASE"),
}


def run_generate_data(engine, users, movies, num_likes):
    try:
        user_ids = engine.insert_users(users)
        if not user_ids:
            raise ValueError("Ошибка вставки пользователей")
        logger.info(f"Добавлено пользователей: {len(user_ids)}")

        movie_ids = engine.insert_movies(movies)
        if not movie_ids:
            raise ValueError("Ошибка вставки фильмов")
        logger.info(f"Добавлено фильмов: {len(movie_ids)}")

        likes = [
            {"user_id": random.choice(user_ids), "movie_id": random.choice(movie_ids)}
            for _ in range(num_likes)
        ]

        engine.insert_likes(likes)
        logger.info(f"Добавлено лайков: {num_likes}")

        return user_ids, movie_ids

    except Exception as e:
        logger.error(f"Ошибка генерации данных: {str(e)}")
        raise RuntimeError("Стоп тест") from e


class RealtimeTester:
    def __init__(self, db_manager, user_ids, movie_ids):
        self.db_manager = db_manager
        self.user_ids = user_ids
        self.movie_ids = movie_ids
        self.query_queue = Queue()
        self.is_running = True
        self.stats = {
            "inserted": 0,
            "errors": 0,
            "query_times": {
                "get_user_likes": [],
                "get_movie_likes_count": [],
                "get_average_rating": [],
            },
        }

    @contextmanager
    def _speed_time(self, operation: str):
        """Змер времени через with"""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            logger.debug(f"{operation} выполнена за {elapsed:.4f}s")

            if operation in self.stats["query_times"]:
                self.stats["query_times"][operation].append(elapsed)

    def _background_insert(self):
        """Фоновая вставка"""
        while self.is_running:
            try:
                data = self._generate_batch(100)
                with self._speed_time("Batch insert"):
                    self.db_manager.insert_likes(data)
                    self.stats["inserted"] += len(data)
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Ошибка вставки: {e}")
            time.sleep(0.1)

    def _query_worker(self):
        """Обработчик запросов"""
        while self.is_running or not self.query_queue.empty():
            try:
                query_type, param = self.query_queue.get(timeout=0.5)

                with self._speed_time(query_type):
                    if query_type == "get_user_likes":
                        self.db_manager.get_user_likes(param)
                    elif query_type == "get_movie_likes_count":
                        self.db_manager.get_movie_likes_count(param)
                    elif query_type == "get_average_rating":
                        self.db_manager.get_average_rating(param)

                self.query_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Ошибка запроса {query_type}: {e}")
                self.stats["errors"] += 1

    def test_under_load(self, duration_sec: int = 60, workers: int = 2):
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
            query_type = random.choice(
                ["get_user_likes", "get_movie_likes_count", "get_average_rating"]
            )
            param = random.randint(1, 1000)
            self.query_queue.put((query_type, param))

        time.sleep(duration_sec)

        self.is_running = False
        for t in worker_threads:
            t.join()

        insert_thread.join()

        # результат по времени
        avg_times = {
            k: sum(v) / len(v) if v else 0 for k, v in self.stats["query_times"].items()
        }
        logger.info(
            f"""
            Результат:
            Вставок: {self.stats['inserted']} (ошибок: {self.stats['errors']})
            Среднее время запроса:
              User likes: {avg_times['get_user_likes']:.4f}s
              Movie likes: {avg_times['get_movie_likes_count']:.4f}s
              Avg rating: {avg_times['get_average_rating']:.4f}s
        """
        )

    def _generate_batch(self, size: int):
        """Генерация данных"""
        return [
            {
                "user_id": random.choice(self.user_ids),
                "movie_id": random.choice(self.movie_ids),
            }
            for _ in range(size)
        ]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # # Тестирование PostgreSQL
    pg_manager = PostgresManager(POSTGRES_CONFIG)
    users, movies = PostgresManager.generate_data(
        num_users=int(os.getenv("NUM_USERS")), num_movies=int(os.getenv("NUM_MOVIES"))
    )
    user_ids, movie_ids = run_generate_data(
        pg_manager, users, movies, int(os.getenv("NUM_LIKES"))
    )

    logger.info("Запуск теста под нагрузкой для PostgreSQL")
    tester = RealtimeTester(pg_manager, user_ids, movie_ids)
    tester.test_under_load(duration_sec=60, workers=2)

    # # Тестирование MongoDB
    mongo_manager = MongoManager(MONGO_CONFIG)
    if not mongo_manager.check_connection():
        logger.error("Cannot connect to MongoDB")
        exit(1)

    users, movies = MongoManager.generate_data(
        num_users=int(os.getenv("NUM_USERS")), num_movies=int(os.getenv("NUM_MOVIES"))
    )
    user_ids, movie_ids = run_generate_data(
        mongo_manager, users, movies, int(os.getenv("NUM_LIKES"))
    )

    logger.info("Запуск теста под нагрузкой для MongoDB")
    tester = RealtimeTester(mongo_manager, user_ids, movie_ids)
    tester.test_under_load(duration_sec=60, workers=2)

    logger.info("Test done")
