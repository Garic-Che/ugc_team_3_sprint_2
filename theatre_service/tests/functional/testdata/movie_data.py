import uuid
from datetime import datetime
import random


def generate_movies_data(movies_len: int = 1):
    movies_data = [
        generate_one_movie_data(movie_title=f"Movie{movie_count}")
        for movie_count in range(movies_len)
    ]
    return movies_data


def generate_one_movie_data(
    movie_id: str = "",
    movie_title: str = "Default Movie",
    imdb_rating: float = None,
    directors_len: int = 1,
    actors_len: int = 2,
    writers_len: int = 2,
    genres_len: int = 2,
):
    movie_id = movie_id or str(uuid.uuid4())
    imdb_rating = (
        imdb_rating
        if imdb_rating is not None
        else round(random.uniform(1, 10), 1)
    )

    directors = [
        {"id": str(uuid.uuid4()), "name": f"Director {i}"}
        for i in range(directors_len)
    ]

    actors = [
        {"id": str(uuid.uuid4()), "name": f"Actor {i}"}
        for i in range(actors_len)
    ]

    writers = [
        {"id": str(uuid.uuid4()), "name": f"Writer {i}"}
        for i in range(writers_len)
    ]

    genres = [
        {
            "name": random.choice(["Comedy", "Drama", "Action"]),
            "uuid": str(uuid.uuid4()),
        }
        for _ in range(genres_len)
    ]

    # Генерация уникального названия с использованием UUID или случайной строки
    unique_title = f"{movie_title}-{uuid.uuid4().hex[:6]}"  # Добавление короткой части UUID для уникальности

    movie_data = {
        "id": movie_id,
        "imdb_rating": imdb_rating,
        "genres": genres,
        "title": unique_title,  # Теперь title уникально
        "description": "Some movie description",
        "directors_names": [d["name"] for d in directors],
        "actors_names": [a["name"] for a in actors],
        "writers_names": [w["name"] for w in writers],
        "directors": directors,
        "actors": actors,
        "writers": writers,
        "access": [],
        "last_change_date": datetime.now().isoformat(),
    }
    return movie_data
