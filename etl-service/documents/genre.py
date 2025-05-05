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

    class Meta:
        dynamic = MetaField("strict")


class Genre(Document):
    id = Keyword()
    name = Text(analyzer="ru_en", fields={"raw": Keyword()})
    description = Text(analyzer="ru_en")
    films = Nested(FilmCommon)
    last_change_date = Keyword(index=False)

    class Index:
        name = "genres"
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


def get_genre_index_data(
    database_settings: dict, last_sync_state: datetime, batch_size: int = 100
) -> Generator[list[Genre], None, None]:
    dsn = make_conninfo(**database_settings)

    with (
        psycopg.connect(dsn, row_factory=class_row(Genre)) as conn,
        ServerCursor(conn, "fetcher") as cursor,
    ):
        raw_sql = """
        SELECT
            g.id,
            g.name,
            COALESCE(g.description, '') as description,
            COALESCE(
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', fw.id,
                    'title', fw.title,
                    'imdb_rating', fw.rating
                )
            ) FILTER (WHERE fw.id IS NOT NULL),
            '[]'
        ) AS films, -- фильмы в формате JSON,
            MAX(v.last_change_date) AS last_change_date -- последняя дата изменения
        FROM content.genre g
        LEFT JOIN content.genre_film_work gfw ON g.id = gfw.genre_id
        LEFT JOIN content.film_work fw ON fw.id = gfw.film_work_id
        CROSS JOIN LATERAL (
            VALUES
                (g.modified),   -- дата изменения жанра
                (gfw.created),  -- дата создания связи жанр-фильм
                (fw.modified)   -- дата изменения фильма
        ) v(last_change_date)
        GROUP BY g.id
        having max(v.last_change_date) > %s
        ORDER BY g.name
        """

        cursor.execute(raw_sql, (last_sync_state,))
        while results := cursor.fetchmany(size=batch_size):
            yield results
