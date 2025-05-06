import uuid
from datetime import datetime
import random


def generate_genres_data(genres_len: int = 1, films_len: int = 1):
    genres_data = [
        generate_one_genre_data(
            genre_name=f"Historical Anarchy {genre_count}", films_len=films_len
        )
        for genre_count in range(genres_len)
    ]
    return genres_data


def generate_one_genre_data(
    genre_id: str = "", genre_name: str = "History", films_len: int = 1
):
    genre_id = genre_id or str(uuid.uuid4())
    genres_data={
        "id": genre_id,
        "name": genre_name,
        "description": "Hello",
        "films": [
            {
                "id": str(uuid.uuid4()),
                "title": f"Star {film_count}",
                "imdb_rating": random.randint(0, 100) / 10,
            }
            for film_count in range(films_len)
        ],
        "last_change_date": datetime.now().isoformat(),
    }
    return genres_data
