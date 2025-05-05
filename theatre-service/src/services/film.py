from functools import lru_cache
from typing import Optional, Dict, Any
from http import HTTPStatus
import logging

from fastapi import Depends, HTTPException

from common.services_functions import make_cache_key, check_access
from db.search_engine import get_search_engine, SearchEngine
from db.cache import get_cache_storage, CacheRules, CacheStorage
from models.models import Film, FilmCommon, FilmList

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
FILM_ES_INDEX = "movies"


class FilmCacheService:
    def __init__(self, cache: CacheStorage, cache_rules: CacheRules):
        self.cache = cache
        self.cache_rules = cache_rules

    async def get_film_from_cache(self, film_id: str) -> Optional[Film]:
        data = await self.cache.get(f"{FILM_ES_INDEX}?{film_id}")
        if not data:
            return None

        film = Film.model_validate_json(data)
        return film

    async def put_film_to_cache(self, film: Film):
        await self.cache.set(
            key=f"{FILM_ES_INDEX}?{film.id}",
            value=film.model_dump_json(),
            expire=FILM_CACHE_EXPIRE_IN_SECONDS,
        )

    async def get_film_list_from_cache(
        self, parameters: Dict[str, Any]
    ) -> list[Optional[FilmCommon]]:
        """Получение списка фильмов по параметрам из кэша"""
        if not self.cache_rules.need_cache(
            parameters.get("page_number", None)
        ):
            return None

        data = await self.cache.get(make_cache_key(FILM_ES_INDEX, parameters))
        if not data:
            return None

        films = FilmList.model_validate_json(data)
        return films.films

    async def put_film_list_to_cache(
        self,
        film_list: list[Optional[FilmCommon]],
        parameters: Dict[str, Any],
    ):
        """Запись списка фильмов по параметрам в кэш"""

        if not self.cache_rules.need_cache(
            parameters.get("page_number", None)
        ):
            return None

        await self.cache.set(
            key=make_cache_key(FILM_ES_INDEX, parameters),
            value=FilmList(films=film_list).model_dump_json(),
            expire=FILM_CACHE_EXPIRE_IN_SECONDS,
        )


class FilmSearchEngineService:
    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    async def get_film_from_search_engine(
        self, film_id: str
    ) -> Optional[Film]:
        if doc := await self.search_engine.get(
            index=FILM_ES_INDEX, id=film_id
        ):
            result = {**doc["_source"]}
            for x in ["directors", "writers", "actors"]:
                result[x] = [
                    {"id": person["id"], "full_name": person["name"]}
                    for person in result[x]
                ]
            logging.debug(f" результат поиска фильма в эластике {result}")
            film = Film(**result)
            return film
        return None

    async def get_similar_films_from_search_engine(
        self, film_id: str, parameters: dict[str, str]
    ) -> list[Optional[FilmCommon]]:
        try:
            # Получаем информацию о фильме
            film_response = await self.search_engine.get(
                index=FILM_ES_INDEX, id=film_id
            )
            if not film_response:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="Film not found"
                )
            film = Film(**film_response["_source"])
            genres_id = [g.model_dump()["uuid"] for g in film.genres]
            logging.debug(f"Genres id of film {film.title}: {genres_id}")

            if not genres_id:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="Film has no genres",
                )

            # Параметры запроса
            page_size = int(parameters.get("page_size", 50))
            page_number = int(parameters.get("page_number", 1))

            response = await self.search_engine.search_similar_films(
                parameters={
                    "page_number": page_number,
                    "page_size": page_size,
                    "genres_id": genres_id,
                    "film_id": film_id,
                },
                index=FILM_ES_INDEX,
            )

            if not response["hits"]["hits"]:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail="Similar films not found",
                )

            # Формируем список фильмов
            films = [
                FilmCommon(
                    id=hit["_id"],
                    title=hit["_source"].get("title"),
                    imdb_rating=hit["_source"].get("imdb_rating"),
                )
                for hit in response["hits"]["hits"]
            ]
            return films

        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
            )

    async def get_films_from_search_engine_by_params(
        self, parameters: dict[str, Any]
    ) -> list[Optional[FilmCommon]]:
        try:
            response = await self.search_engine.search_films_by_params(
                parameters=parameters, index=FILM_ES_INDEX
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
            )

        if not response["hits"]["hits"]:
            return []

        # Формируем список фильмов
        films = [
            FilmCommon(
                id=hit["_id"],
                title=hit["_source"].get("title"),
                imdb_rating=hit["_source"].get("imdb_rating"),
            )
            for hit in response["hits"]["hits"]
        ]
        return films


class FilmService:
    def __init__(
        self,
        cache_service: FilmCacheService,
        search_engine_service: FilmSearchEngineService,
    ):
        self.cache_service = cache_service
        self.search_engine_service = search_engine_service

    async def get_by_id(
        self, film_id: str, roles: list[str]
    ) -> Optional[Film]:
        """Возвращает объект фильма.
        Он опционален, так как фильм может отсутствовать в базе"""
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        film = await self.cache_service.get_film_from_cache(film_id)
        if not film:
            # Если фильма нет в кеше, то ищем его в search_engine
            film = (
                await self.search_engine_service.get_film_from_search_engine(
                    film_id
                )
            )
            if not film or (
                film.access and not await check_access(film.access, roles)
            ):
                # Если он отсутствует в search_engine,
                # значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self.cache_service.put_film_to_cache(film)

        return film

    async def get_similar_films_by_id(
        self, film_id: str, parameters: dict[str, str]
    ) -> Optional[list[Any]]:
        """Возвращает список объектов фильмов похожих на фильм"""
        films = await self.cache_service.get_film_list_from_cache(parameters)
        if films is None:
            films = await self.search_engine_service.get_similar_films_from_search_engine(
                film_id, parameters
            )
            if films is None:
                return None
            await self.cache_service.put_film_list_to_cache(films, parameters)
        return films

    async def get_by_parameters(
        self, parameters: dict[str, str]
    ) -> Optional[list[Any]]:
        """Возвращает список объектов фильма"""
        films = await self.cache_service.get_film_list_from_cache(parameters)
        if films is None:
            films = await self.search_engine_service.get_films_from_search_engine_by_params(
                parameters
            )
            if films is None:
                return None
            await self.cache_service.put_film_list_to_cache(films, parameters)
        return films


@lru_cache()
def get_film_service(
    cache_storage: CacheStorage = Depends(get_cache_storage),
    search_engine: SearchEngine = Depends(get_search_engine),
) -> FilmService:
    cache_service = FilmCacheService(
        cache=cache_storage, cache_rules=CacheRules()
    )
    search_engine_service = FilmSearchEngineService(search_engine)
    return FilmService(cache_service, search_engine_service)
