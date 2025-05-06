from functools import lru_cache
from typing import Optional, Dict, Any
from http import HTTPStatus

from fastapi import Depends, HTTPException

from common.services_functions import make_cache_key
from db.cache import CacheRules, CacheStorage, get_cache_storage
from db.search_engine import get_search_engine, SearchEngine
from models.models import (
    Person,
    FilmOfPerson,
    PersonList,
)

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
PERSON_ES_INDEX = "persons"


class PersonCacheService:
    def __init__(self, cache: CacheStorage, cache_rules: CacheRules):
        self.cache = cache
        self.cache_rules = cache_rules

    async def get_person_list_from_cache(
        self, parameters: Dict[str, Any]
    ) -> list[Optional[Person]]:
        """Получение списка персон по параметрам из кэша"""
        if not self.cache_rules.need_cache(
            parameters.get("page_number", None)
        ):
            return None

        data = await self.cache.get(
            make_cache_key(PERSON_ES_INDEX, parameters)
        )
        if not data:
            return None

        persons = PersonList.model_validate_json(data)
        return persons.persons

    async def put_person_list_to_cache(
        self,
        person_list: list[Optional[Person]],
        parameters: Dict[str, Any],
    ):
        """Запись списка персон по параметрам в кэш"""
        if not self.cache_rules.need_cache(
            parameters.get("page_number", None)
        ):
            return None

        await self.cache.set(
            key=make_cache_key(PERSON_ES_INDEX, parameters),
            value=PersonList(persons=person_list).model_dump_json(),
            expire=PERSON_CACHE_EXPIRE_IN_SECONDS,
        )

    async def get_person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.cache.get(f"{PERSON_ES_INDEX}?{person_id}")
        if not data:
            return None

        person = Person.model_validate_json(data)
        return person

    async def put_person_to_cache(self, person: Person):
        await self.cache.set(
            key=f"{PERSON_ES_INDEX}?{person.id}",
            value=person.model_dump_json(),
            expire=PERSON_CACHE_EXPIRE_IN_SECONDS,
        )


class PersonSearchEngineService:
    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    async def get_persons_from_search_engine(
        self, parameters: dict
    ) -> list[Person]:
        """Поиск по параметрам (например, имя, пагинация)."""
        try:
            response = await self.search_engine.search_persons_by_params(
                parameters, PERSON_ES_INDEX
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
            )

        if not response["hits"]["hits"]:
            return []

        # Формируем список персон с фильмами
        persons = [
            Person(
                id=hit["_id"],
                full_name=hit["_source"].get("full_name"),
                films=[
                    FilmOfPerson(
                        id=f["id"], roles=f["roles"]
                    )  # Преобразуем в FilmOfPerson
                    for f in hit["_source"].get("films", [])
                ],
            )
            for hit in response["hits"]["hits"]
        ]
        return persons

    async def get_person_from_search_engine(
        self, person_id: str
    ) -> Optional[Person]:
        doc = await self.search_engine.get(index=PERSON_ES_INDEX, id=person_id)
        if not doc:
            return None
        return Person(**doc["_source"])


class PersonService:
    def __init__(
        self,
        cache_service: PersonCacheService,
        search_engine_service: PersonSearchEngineService,
    ):
        self.cache_service = cache_service
        self.search_engine_service = search_engine_service

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        """Возвращает объект персоны.
        Он опционален, так как персона может отсутствовать в базе"""
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        person = await self.cache_service.get_person_from_cache(person_id)
        if not person:
            # Если персоны нет в кеше, то ищем его в search_engine
            person = (
                await self.search_engine_service.get_person_from_search_engine(
                    person_id
                )
            )
            if not person:
                # Если он отсутствует в search_engine,
                # значит, персоны вообще нет в базе
                return None
            # Сохраняем персону в кеш
            await self.cache_service.put_person_to_cache(person)

        return person

    async def get_by_parameters(
        self, parameters: dict[str, str]
    ) -> list[Optional[Person]]:
        """Возвращает список объектов персон"""
        persons = await self.cache_service.get_person_list_from_cache(
            parameters
        )
        if persons is None:
            persons = await self.search_engine_service.get_persons_from_search_engine(
                parameters
            )
            if persons is None:
                return None
            await self.cache_service.put_person_list_to_cache(
                persons, parameters
            )
        return persons


@lru_cache()
def get_person_service(
    cache_storage: CacheStorage = Depends(get_cache_storage),
    search_engine: SearchEngine = Depends(get_search_engine),
) -> PersonService:
    cache_service = PersonCacheService(
        cache=cache_storage, cache_rules=CacheRules()
    )
    search_engine_service = PersonSearchEngineService(search_engine)
    return PersonService(cache_service, search_engine_service)
