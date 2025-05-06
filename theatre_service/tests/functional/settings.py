from pydantic_settings import BaseSettings

from tests.functional.testdata.es_mapping import (
    MOVIES_MAPPING,
    GENRES_MAPPING,
    PERSONS_MAPPING,
)
from tests.functional.utils.helpers import (
    RedisSettings,
    ElasticsearchSettings,
    ServiceSettings,
)


es_settings = ElasticsearchSettings()
redis_settings = RedisSettings()
service_settings = ServiceSettings()


class TestSettings(BaseSettings):
    es_url: str = es_settings.get_host()
    es_index: str = ...
    es_index_mapping: dict = ...

    redis_url: str = redis_settings.get_host()
    service_url: str = service_settings.get_host()


test_film_settings = TestSettings(es_index="movies", es_index_mapping=MOVIES_MAPPING)


test_genre_settings = TestSettings(es_index="genres", es_index_mapping=GENRES_MAPPING)


test_person_settings = TestSettings(
    es_index="persons", es_index_mapping=PERSONS_MAPPING
)


test_search_settings = TestSettings(es_index="movies", es_index_mapping=MOVIES_MAPPING)
