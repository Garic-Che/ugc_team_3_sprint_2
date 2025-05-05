from datetime import datetime
from typing import Generator

import psycopg
from elasticsearch_dsl import (
    Document,
    Float,
    InnerDoc,
    Keyword,
    MetaField,
    Nested,
    Text,
)
from psycopg import ServerCursor
from psycopg.conninfo import make_conninfo
from psycopg.rows import class_row


class FilmCommon(InnerDoc):
    id = Keyword()
    title = Text(analyzer="ru_en")
    imdb_rating = Float()
    roles = Keyword(multi=True)

    class Meta:
        dynamic = MetaField("strict")


class Person(Document):
    id = Keyword()
    full_name = Text(analyzer="ru_en", fields={"raw": Keyword()})
    films = Nested(FilmCommon)
    last_change_date = Keyword(index=False)

    class Index:
        name = "persons"
        settings = {
            "refresh_interval": "1s",
            "analysis": {
                "filter": {
                    "english_stop": {"type": "stop", "stopwords": "_english_"},
                    "english_stemmer": {
                        "type": "stemmer",
                        "language": "english",
                    },
                    "english_possessive_stemmer": {
                        "type": "stemmer",
                        "language": "possessive_english",
                    },
                    "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                    "russian_stemmer": {
                        "type": "stemmer",
                        "language": "russian",
                    },
                },
                "analyzer": {
                    "ru_en": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "english_stop",
                            "english_stemmer",
                            "english_possessive_stemmer",
                            "russian_stop",
                            "russian_stemmer",
                        ],
                    }
                },
            },
        }

    class Meta:
        dynamic = MetaField("strict")


def get_person_index_data(
    database_settings: dict, last_sync_state: datetime, batch_size: int = 100
) -> Generator[list[Person], None, None]:
    dsn = make_conninfo(**database_settings)

    with (
        psycopg.connect(dsn, row_factory=class_row(Person)) as conn,
        ServerCursor(conn, "fetcher") as cursor,
    ):
        raw_sql = """
        WITH film_roles AS (
            SELECT
                pfw.person_id,
                fw.id AS film_id,
                fw.title,
                fw.rating,
                ARRAY_AGG(DISTINCT pfw.role) AS roles,
                MAX(fw.modified) AS film_modified
            FROM content.person_film_work pfw
            JOIN content.film_work fw ON fw.id = pfw.film_work_id
            GROUP BY pfw.person_id, fw.id, fw.title, fw.rating
        )
        SELECT
            p.id,
            p.full_name,
            COALESCE(
                jsonb_agg(
                    DISTINCT jsonb_build_object(
                        'id', fr.film_id,
                        'title', fr.title,
                        'imdb_rating', fr.rating,
                        'roles', fr.roles
                    )
                ) FILTER (WHERE fr.film_id IS NOT NULL),
                '[]'
            ) AS films,
            MAX(v.last_change_date) AS last_change_date
        FROM content.person p
        LEFT JOIN film_roles fr ON p.id = fr.person_id
        CROSS JOIN LATERAL (
            VALUES
                (p.modified),
                (fr.film_modified)
        ) v(last_change_date)
        GROUP BY p.id
        having max(v.last_change_date) > %s
        ORDER BY p.full_name
        """

        cursor.execute(raw_sql, (last_sync_state,))
        while results := cursor.fetchmany(size=batch_size):
            yield results
