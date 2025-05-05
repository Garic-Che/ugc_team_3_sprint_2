MOVIES_MAPPING = {
    "settings": {
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
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "actors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "actors_names": {"type": "text", "analyzer": "ru_en"},
            "description": {"type": "text", "analyzer": "ru_en"},
            "directors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "directors_names": {"type": "text", "analyzer": "ru_en"},
            "genres": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "name": {"type": "text", "analyzer": "ru_en"},
                    "uuid": {"type": "keyword"},
                },
            },
            "id": {"type": "keyword"},
            "imdb_rating": {"type": "float"},
            "last_change_date": {"type": "keyword", "index": False},
            "title": {
                "type": "text",
                "fields": {"raw": {"type": "keyword"}},
                "analyzer": "ru_en",
            },
            "writers": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "writers_names": {"type": "text", "analyzer": "ru_en"},
            "access": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "privilege": {"type": "keyword"},
                },
            },
        },
    },
}
GENRES_MAPPING = {
    "settings": {
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
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "description": {"type": "text", "analyzer": "ru_en"},
            "films": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "imdb_rating": {"type": "float"},
                    "title": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "id": {"type": "keyword"},
            "last_change_date": {"type": "keyword", "index": False},
            "name": {
                "type": "text",
                "fields": {"raw": {"type": "keyword"}},
                "analyzer": "ru_en",
            },
        },
    },
}
PERSONS_MAPPING = {
    "settings": {
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
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "films": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "imdb_rating": {"type": "float"},
                    "roles": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "full_name": {
                "type": "text",
                "fields": {"raw": {"type": "keyword"}},
                "analyzer": "ru_en",
            },
            "id": {"type": "keyword"},
            "last_change_date": {"type": "keyword", "index": False},
        },
    },
}
