import logging
import time
import psycopg2
from contextlib import contextmanager
from faker import Faker
from functools import wraps
from typing import List
from psycopg2 import extras


logger = logging.getLogger(__name__)

QUERY_INSERT_USERS = "INSERT INTO users (username) VALUES (%s) RETURNING id"
QUERY_INSERT_MOVIES = "INSERT INTO movies (title) VALUES (%s)"
QUERY_COUNT_LIKES = "SELECT likes_count FROM movies WHERE id = %s"
QUERY_INSERT_LIKES = """
    INSERT INTO likes (user_id, movie_id)
    VALUES %s
    ON CONFLICT (user_id, movie_id) DO NOTHING
"""
QUERY_SELECT_LIKES = "SELECT movie_id FROM likes WHERE user_id = %s"


class PostgresManager:
    def __init__(self, config):
        self.config = config

    @contextmanager
    def connection(self):
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            yield conn
        except Exception as e:
            logger.error(f"Connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

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
    def insert_users(self, data: List):
        """Вставка пользователей"""
        if not data:
            logger.warning("Пустой список пользователей")
            return []

        try:
            with self.connection() as conn:
                cur = conn.cursor()

                unique_users = {u["username"]: u for u in data}
                usernames = list(unique_users.keys())

                if not usernames:
                    logger.info("Пустой список уникальных пользователей")
                    return []

                usernames_data = ", ".join(["(%s)"] * len(usernames))
                query = f"""
                    INSERT INTO users (username)
                    VALUES {usernames_data}
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id
                """

                cur.execute(query, usernames)
                inserted_ids = [row[0] for row in cur.fetchall()]
                conn.commit()

                logger.info(
                    f"Добавлено {len(inserted_ids)} пользователей из {len(data)}"
                )
                return inserted_ids

        except Exception as e:
            logger.error(f"Ошибка вставки пользователей: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return []

    @speed_time
    def insert_movies(self, data: List):
        """Улучшенная вставка фильмов"""
        if not data:
            logger.warning("Пустой список фильмов")
            return []

        try:
            with self.connection() as conn:
                cur = conn.cursor()

                unique_movies = {m["title"]: m for m in data}
                titles = list(unique_movies.keys())

                if not titles:
                    logger.info("Пустой список уникальных фильмов")
                    return []

                titles_data = ", ".join(["(%s)"] * len(titles))
                query = f"""
                    INSERT INTO movies (title)
                    VALUES {titles_data}
                    ON CONFLICT (title) DO NOTHING
                    RETURNING id
                """

                cur.execute(query, titles)
                inserted_ids = [row[0] for row in cur.fetchall()]
                conn.commit()

                logger.info(f"Добавлено {len(inserted_ids)} фильмов из {len(data)}")
                return inserted_ids

        except Exception as e:
            logger.error(f"Ошибка вставки фильмов: {e}", exc_info=True)
            if conn:
                conn.rollback()
            return []

    @speed_time
    def insert_likes(self, data: List):
        if not data:
            logger.warning("Пустого списка лайков")
            return

        try:
            with self.connection() as conn:
                cur = conn.cursor()
                likes_data = [(d["user_id"], d["movie_id"]) for d in data]
                query = QUERY_INSERT_LIKES
                extras.execute_values(
                    cur, query, likes_data, template="(%s, %s)", page_size=1000
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка вставки лайков: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise

    @speed_time
    def get_user_likes(self, user_id):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(QUERY_SELECT_LIKES, (user_id,))
                return cur.fetchall()

    @speed_time
    def get_movie_likes_count(self, movie_id: int):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT likes_count FROM movies WHERE id = %s", (movie_id,))
                result = cur.fetchone()
                return result[0] if result else 0

    @speed_time
    def get_average_rating(self, movie_id: int):
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0] or 1
                cur.execute("SELECT likes_count FROM movies WHERE id = %s", (movie_id,))
                result = cur.fetchone()
                likes = result[0] if result else 0
                return likes / total_users

    @staticmethod
    def generate_data(num_users, num_movies):
        fake = Faker()

        users = []
        unique_usernames = set()
        while len(users) < num_users:
            username = fake.user_name()
            if username not in unique_usernames:
                unique_usernames.add(username)
                users.append({"username": username})

        movies = []
        unique_titles = set()
        while len(movies) < num_movies:
            title = fake.sentence(nb_words=3)
            if title not in unique_titles:
                unique_titles.add(title)
                movies.append({"title": title})

        return (users, movies)
