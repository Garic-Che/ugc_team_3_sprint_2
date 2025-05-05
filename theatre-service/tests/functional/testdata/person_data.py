import uuid
from datetime import datetime
import random


def generate_persons_data(persons_len: int = 1, films_len: int = 1):
    persons_data = [
        generate_one_person_data(
            person_name=f"Erol Otus{person_count}", films_len=films_len
        )
        for person_count in range(persons_len)
    ]
    return persons_data


def generate_one_person_data(
    person_id: str = "", person_name: str = "Erol Otus", films_len: int = 1
):
    person_id = person_id or str(uuid.uuid4())
    person_data = {
        "id": person_id,
        "full_name": person_name,
        "films": [
            {
                "id": str(uuid.uuid4()),
                "roles": random.choices(
                    ["actor", "writer", "director"], k=random.randint(0, 3)
                ),
                "title": f"Star {film_count}",
                "imdb_rating": (films_len - film_count) * 10 / films_len,
            }
            for film_count in range(films_len)
        ],
        "last_change_date": datetime.now().isoformat(),
    }
    return person_data


def es_bulk_query(es_data: list[dict], es_index: str):
    bulk_query: list[dict] = []
    for row in es_data:
        data = {"_index": es_index, "_id": row["id"]}
        data.update({"_source": row})
        bulk_query.append(data)
    return bulk_query
