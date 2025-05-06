from functools import lru_cache
from typing import Optional, Dict, Any
from http import HTTPStatus

from fastapi import Depends, HTTPException

from common.services_functions import make_cache_key
from db.search_engine import get_search_engine, SearchEngine
from db.cache import CacheRules, CacheStorage, get_cache_storage
from models.models import Genre, GenreCommon, FilmCommon, GenreList

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
GENRE_ES_INDEX = "genres"


class GenreCacheService:
    def __init__(self, cache: CacheStorage, cache_rules: CacheRules):
        self.cache = cache
        self.cache_rules = cache_rules

    async def get_genre_list_from_cache(
        self, parameters: Dict[str, Any]
    ) -> list[Optional[Genre]]:
        """Получение списка жанров по параметрам из кэша"""
        if not self.cache_rules.need_cache(
            parameters.get("page_number", None)
        ):
            return None

        data = await self.cache.get(make_cache_key(GENRE_ES_INDEX, parameters))
        if not data:
            return None

        genres = GenreList.model_validate_json(data)
        return genres.genres

    async def put_genre_list_to_cache(
        self,
        genre_list: list[Optional[GenreCommon]],
        parameters: Dict[str, Any],
    ):
        """Запись списка жанров по параметрам в кэш"""
        if not self.cache_rules.need_cache(
            parameters.get("page_number", None)
        ):
            return None

        await self.cache.set(
            key=make_cache_key(GENRE_ES_INDEX, parameters),
            value=GenreList(genres=genre_list).model_dump_json(),
            expire=GENRE_CACHE_EXPIRE_IN_SECONDS,
        )

    async def get_genre_from_cache(
        self, genre_id: str, parameters: Dict[str, Any]
    ) -> Optional[Genre]:
        key = make_cache_key(f"{GENRE_ES_INDEX}?{genre_id}", parameters)
        data = await self.cache.get(key)
        if not data:
            return None

        genre = Genre.model_validate_json(data)
        return genre

    async def put_genre_to_cache(
        self, genre: Genre, parameters: Dict[str, Any]
    ):
        key = make_cache_key(f"{GENRE_ES_INDEX}?{genre.uuid}", parameters)
        await self.cache.set(
            key,
            genre.model_dump_json(),
            GENRE_CACHE_EXPIRE_IN_SECONDS,
        )


class GenreSearchEngineService:
    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    async def get_genres_from_search_engine(
        self, parameters: dict[str, str]
    ) -> list[GenreCommon]:
        try:
            response = await self.search_engine.search_genres_by_params(
                parameters, GENRE_ES_INDEX
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
            )

        if not response["hits"]["hits"]:
            return []

        # Создание объектов GenreCommon без поля description
        genres = [
            GenreCommon(
                uuid=hit["_id"],
                name=hit["_source"].get("name"),
            )
            for hit in response["hits"]["hits"]
        ]
        return genres

    async def get_genre_from_search_engine(
        self, genre_id: str, page_size: int, page_number: int, sort: str
    ) -> Optional[Genre]:
        """Получаем жанр и связанные с ним фильмы из search_engine."""

        doc = await self.search_engine.get(index=GENRE_ES_INDEX, id=genre_id)
        if not doc:
            return None

        genre_data = doc["_source"]

        # Пагинация и сортировка фильмов
        films = genre_data.get("films", [])

        # Сортировка по полю imdb_rating
        if sort == "-imdb_rating":
            films = sorted(
                films, key=lambda f: f.get("imdb_rating", 0), reverse=True
            )
        elif sort == "imdb_rating":
            films = sorted(films, key=lambda f: f.get("imdb_rating", 0))

        # Пагинация
        from_ = (page_number - 1) * page_size
        films = films[from_ : from_ + page_size]

        # Возвращаем объект жанра с фильмами
        return Genre(
            uuid=genre_data.get("id"),
            name=genre_data.get("name"),
            films=[
                FilmCommon(
                    id=film.get("id"),
                    title=film.get("title"),
                    imdb_rating=film.get("imdb_rating"),
                )
                for film in films
            ],
        )


class GenreService:
    def __init__(
        self,
        cache_service: GenreCacheService,
        search_engine_service: GenreSearchEngineService,
    ):
        self.cache_service = cache_service
        self.search_engine_service = search_engine_service

    async def get_by_id(
        self, genre_id: str, parameters: dict[str, str]
    ) -> Optional[Genre]:
        """Возвращает жанр с фильмами, сортируя и применяя пагинацию."""

        # Пытаемся получить данные жанра из кеша
        genre = await self.cache_service.get_genre_from_cache(
            genre_id, parameters
        )

        if not genre:
            # Если жанра нет в кеше, ищем его в search_engine
            genre = (
                await self.search_engine_service.get_genre_from_search_engine(
                    genre_id, **parameters
                )
            )

            if not genre:
                # Если жанр не найден в search_engine, возвращаем None
                return None

            # Если жанр найден, сохраняем его в кеш
            await self.cache_service.put_genre_to_cache(genre, parameters)

        # Возвращаем жанр с фильмами
        return genre

    async def get_by_parameters(
        self, parameters: dict[str, str]
    ) -> list[GenreCommon]:
        genres = await self.cache_service.get_genre_list_from_cache(parameters)
        if genres is None:
            genres = (
                await self.search_engine_service.get_genres_from_search_engine(
                    parameters
                )
            )
            if genres is None:
                return None
            await self.cache_service.put_genre_list_to_cache(
                genres, parameters
            )
        return genres


@lru_cache()
def get_genre_service(
    cache_storage: CacheStorage = Depends(get_cache_storage),
    search_engine: SearchEngine = Depends(get_search_engine),
) -> GenreService:
    cache_service = GenreCacheService(
        cache=cache_storage, cache_rules=CacheRules()
    )
    search_engine_service = GenreSearchEngineService(search_engine)
    return GenreService(cache_service, search_engine_service)
