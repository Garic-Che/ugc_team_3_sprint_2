from typing import Dict, Any

from elastic_transport import ObjectApiResponse
from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.exceptions import ConnectionError
import backoff

from .search_engine import SearchEngine
from core import config


class ElasticsearchEngine(SearchEngine):
    def __init__(self, hosts: list[str]):
        self.client = AsyncElasticsearch(hosts=hosts)

    @backoff.on_exception(backoff.expo, exception=ConnectionError, max_time=60)
    async def search(self, index: str, body: Dict) -> ObjectApiResponse:
        response = await self.client.search(index=index, body=body)
        return response

    @backoff.on_exception(backoff.expo, exception=ConnectionError, max_time=60)
    async def get(self, index: str, id: str) -> ObjectApiResponse:
        try:
            response = await self.client.get(index=index, id=id)
            return response
        except NotFoundError:
            return None

    def film_parameters_to_body(
        self, parameters: dict[str, Any], query: dict[str, Any]
    ) -> dict:
        order = parameters.get("sort_order", "desc")
        body = {
            "from": (parameters["page_number"] - 1) * parameters["page_size"],
            "size": parameters["page_size"],
            "query": query,
            "sort": [{"imdb_rating": {"order": order}}],
        }
        return body

    def genre_parameters_to_body(
        self, parameters: dict[str, Any], query: dict[str, Any]
    ) -> dict:
        body = {
            "from": (parameters["page_number"] - 1) * parameters["page_size"],
            "size": parameters["page_size"],
            "query": query,
        }
        return body

    def person_parameters_to_body(
        self, parameters: dict[str, Any], query: dict[str, Any]
    ) -> dict:
        # order = parameters.get("sort_order", "desc")
        body = {
            "from": (parameters["page_number"] - 1) * parameters["page_size"],
            "size": parameters["page_size"],
            "query": query,
            # "sort": [{"full_name": {"order": order}}]
        }
        return body

    def make_similar_films_query(self, parameters):
        query = {
            "nested": {
                "path": "genres",
                "query": {
                    "bool": {
                        "should": [
                            {"term": {"genres.uuid": genre}}
                            for genre in parameters["genres_id"]
                        ],
                        "minimum_should_match": 1,
                        "must_not": [],
                    }
                },
            }
        }
        if parameters["film_id"]:
            # Исключаем текущий фильм
            query["nested"]["query"]["bool"]["must_not"] = [
                {"term": {"_id": parameters["film_id"]}}
            ]
        return query

    def make_film_query_by_params(self, parameters: dict[str, Any]) -> dict:
        query = {"bool": {"must": []}}
        genres_query = {
            "nested": {"path": "genres", "query": {"bool": {"must": []}}}
        }
        # Фильтр по жанру
        if parameters.get("genre_id"):
            genres_query["nested"]["query"]["bool"]["must"].append(
                {"term": {"genres.uuid": parameters["genre_id"]}}
            )

        # Поиск по запросу (название или описание)
        if parameters.get("query"):
            query["bool"]["must"].append(
                {
                    "multi_match": {
                        "query": parameters["query"],
                        "fields": ["title", "description"],
                    }
                }
            )

        final_query = {"bool": {"must": [query]}}
        if parameters.get("genre_id"):
            final_query["bool"]["must"].append(genres_query)

        return final_query

    async def search_similar_films(
        self, parameters: dict[str, Any], index: str
    ):
        body = self.film_parameters_to_body(
            parameters=parameters,
            query=self.make_similar_films_query(parameters),
        )
        return await self.search(index=index, body=body)

    async def search_films_by_params(
        self, parameters: dict[str, Any], index: str
    ):
        body = self.film_parameters_to_body(
            parameters=parameters,
            query=self.make_film_query_by_params(parameters),
        )
        return await self.search(index=index, body=body)

    async def search_genres_by_params(
        self, parameters: dict[str, Any], index: str
    ):
        body = self.genre_parameters_to_body(
            parameters=parameters,
            query=self.make_genres_query_by_params(parameters),
        )
        return await self.search(index=index, body=body)

    def make_genres_query_by_params(self, parameters: dict[str, Any]):
        query = {"bool": {"must": []}}

        # Фильтрация по имени жанра
        if parameters.get("query"):
            query["bool"]["must"].append(
                {
                    "match": {
                        "name": {
                            "query": parameters["query"],
                            "fuzziness": "AUTO",
                        }
                    }
                }
            )
        return query

    def make_persons_query_by_params(self, parameters: dict[str, Any]):
        query = {"bool": {"must": []}}

        # Поиск по имени
        if parameters.get("query"):
            query["bool"]["must"].append(
                {
                    "multi_match": {
                        "query": parameters["query"],
                        "fields": ["full_name"],
                    }
                }
            )
        return query

    async def search_persons_by_params(
        self, parameters: dict[str, Any], index: str
    ):
        body = self.person_parameters_to_body(
            parameters=parameters,
            query=self.make_persons_query_by_params(parameters),
        )
        return await self.search(index=index, body=body)


async def init_elastic() -> ElasticsearchEngine:
    hosts = [
        f"{config.settings.es_schema}{config.settings.es_host}:{config.settings.es_port}"
    ]
    engine = ElasticsearchEngine(hosts=hosts)
    await engine.client.ping()
    return engine
