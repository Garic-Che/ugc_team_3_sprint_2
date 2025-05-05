from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class SearchEngine(ABC):
    @abstractmethod
    async def search(self, index: str, body: Dict):
        pass

    @abstractmethod
    async def get(self, index: str, id: str):
        pass

    @abstractmethod
    def film_parameters_to_body(
        self, parameters: dict[str, Any], query: dict[str, Any]
    ) -> dict:
        pass

    @abstractmethod
    def genre_parameters_to_body(
        self, parameters: dict[str, Any], query: dict[str, Any]
    ) -> dict:
        pass

    @abstractmethod
    def person_parameters_to_body(
        self, parameters: dict[str, Any], query: dict[str, Any]
    ) -> dict:
        pass

    @abstractmethod
    async def search_similar_films(
        self, parameters: dict[str, Any], index: str
    ):
        pass

    @abstractmethod
    def make_similar_films_query(self, parameters: dict[str, Any]):
        pass

    @abstractmethod
    def make_film_query_by_params(self, parameters: dict[str, Any]):
        pass

    @abstractmethod
    async def search_films_by_params(
        self, parameters: dict[str, Any], index: str
    ):
        pass

    @abstractmethod
    async def search_genres_by_params(
        self, parameters: dict[str, Any], index: str
    ):
        pass

    @abstractmethod
    async def make_genres_query_by_params(self, parameters: dict[str, Any]):
        pass

    @abstractmethod
    async def search_persons_by_params(
        self, parameters: dict[str, Any], index: str
    ):
        pass

    @abstractmethod
    async def make_persons_query_by_params(self, parameters: dict[str, Any]):
        pass


async def get_search_engine() -> SearchEngine:
    return engine


engine: Optional[SearchEngine] = None
