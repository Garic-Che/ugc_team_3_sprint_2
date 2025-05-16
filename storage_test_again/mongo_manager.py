import logging
import time
import random
from contextlib import contextmanager
from functools import wraps
from faker import Faker
from typing import List
from pymongo import MongoClient, InsertOne, UpdateOne

logger = logging.getLogger(__name__)


class MongoManager:
    def __init__(self, config):
        self.config = config

    @contextmanager
    def connection(self):
        try:
            client = MongoClient(
                host=self.config["host"],
                port=self.config["port"],
                username=self.config["user"],
                password=self.config["password"],
                authSource="admin",
                maxPoolSize=100,  # Увеличьте размер пула
                connectTimeoutMS=30000,
            )
            db = client[self.config["database"]]
            yield db
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")

    def check_connection(self):
        """Проверка подключения"""
        try:
            with self.connection() as conn:
                conn.command("ping")
                return True
        except Exception as e:
            logger.error(f"Ошибка подключения: {str(e)}")
            return False

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

    @speed_time
    def insert_users(self, data):
        """Вставка пользователей"""
        try:
            with self.connection() as conn_db:
                for doc in data:
                    doc["_id"] = doc.get("_id", random.randint(1, 10**6))

                result = conn_db.users.bulk_write(
                    [InsertOne(doc) for doc in data], ordered=False
                )
                logger.info(f"Успешно вставлено {len(data)} пользователей")
                return [doc["_id"] for doc in data]

        except Exception as e:
            logger.error(f"Ошибка вставки пользователей: {str(e)}")
            return []

    @speed_time
    def insert_movies(self, data):
        """Вставка фильмов"""
        try:
            with self.connection() as conn_db:
                for doc in data:
                    doc["_id"] = doc.get("_id", random.randint(1, 10**6))
                    doc["likes_count"] = doc.get("likes_count", 0)

                result = conn_db.movies.bulk_write(
                    [InsertOne(doc) for doc in data], ordered=False
                )
                logger.info(f"Успешно вставлено {len(data)} фильмов")
                return [doc["_id"] for doc in data]

        except Exception as e:
            logger.error(f"Ошибка вставки фильмов: {str(e)}")
            return []

    @speed_time
    def insert_likes(self, data):
        user_ops = []
        movie_ops = []

        for like in data:
            user_ops.append(
                UpdateOne(
                    {"_id": like["user_id"]},
                    {"$addToSet": {"likes": like["movie_id"]}},
                    upsert=False,
                )
            )
            movie_ops.append(
                UpdateOne(
                    {"_id": like["movie_id"]},
                    {"$inc": {"likes_count": 1}},
                    upsert=False,
                )
            )

        try:
            with self.connection() as conn_db:
                users_result = conn_db.users.bulk_write(user_ops, ordered=False)
                movies_result = conn_db.movies.bulk_write(movie_ops, ordered=False)
        except Exception as e:
            logger.error(f"Ошибка вставки лайков: {e}")
            raise

    def get_user_likes(self, user_id: int) -> List[int]:
        with self.connection() as conn_db:
            # user = conn_db.users.find_one({"_id": user_id})
            user = conn_db.users.find_one(
                {"_id": user_id},
                {"_id": 0, "likes": 1},  # Возвращаем только нужные поля
            )
            return user.get("likes", []) if user else []

    def get_movie_likes_count(self, movie_id: int) -> int:
        with self.connection() as conn_db:
            movie = conn_db.movies.find_one({"_id": movie_id})
            return movie.get("likes_count", 0) if movie else 0

    # def get_average_rating(self, movie_id: int) -> float:
    #     with self.connection() as conn_db:
    #         total_users = conn_db.users.count_documents({})
    #         likes = self.get_movie_likes_count(movie_id)
    #         return likes / total_users if total_users else 0

    def get_average_rating(self, movie_id: int) -> float:
        with self.connection() as conn_db:
            total_users = conn_db.users.estimated_document_count()
            likes = self.get_movie_likes_count(movie_id)
            return likes / total_users if total_users else 0

    @staticmethod
    def generate_data(num_users, num_movies):
        """Генерация данных"""
        fake = Faker()
        return (
            [{"_id": i, "username": fake.user_name()} for i in range(1, num_users + 1)],
            [
                {"_id": i, "title": fake.sentence(nb_words=3)}
                for i in range(1, num_movies + 1)
            ],
        )
