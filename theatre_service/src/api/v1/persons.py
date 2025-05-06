from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query

from services.person import PersonService, get_person_service
from api.v1.schemes import FilmCommon, FilmOfPerson, PersonCommon, Person
from api.v1.pagination import PaginatedParams

router = APIRouter()


@router.get(
    "/",
    response_model=list[PersonCommon],
    summary="Показ списка персон",
)
@router.get(
    "/search",
    response_model=list[Person],
    summary="Поиск по людям",
)
async def persons_list(
    query: str = Query(
        default=None, description="Поиск по названию или описанию"
    ),
    pagination: PaginatedParams = Depends(),
    sort: str = Query(default="-full_name", description="Сортировка по имени"),
    person_service: PersonService = Depends(get_person_service),
) -> list[Person]:
    # Параметры запроса
    parameters = {
        "query": query,  # Поиск по имени
        "page_size": pagination.page_size,
        "page_number": pagination.page_number,
        "sort": sort,  # Сортировка
    }

    # Получаем данные через сервис
    persons = await person_service.get_by_parameters(parameters)
    if not persons:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="persons not found"
        )

    return [
        Person(
            uuid=person.id,
            full_name=person.full_name,
            films=[
                FilmOfPerson(uuid=f.id, roles=f.roles) for f in person.films
            ],
        )
        for person in persons
    ]  # Возвращаем уже список объектов Person, а не PersonCommon


@router.get(
    "/{person_id}",
    response_model=Person,
    summary="Данные по конкретному человеку",
)
async def person_details(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="person not found"
        )

    return Person(
        uuid=person.id,
        full_name=person.full_name,
        films=[FilmOfPerson(uuid=f.id, roles=f.roles) for f in person.films],
    )


@router.get(
    "/{person_id}/films",
    response_model=list[FilmCommon],
    summary="Список фильмов персоны",
)
async def person_films_list(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
) -> list[FilmCommon]:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="person not found"
        )

    return [
        FilmCommon(uuid=f.id, title=f.title, imdb_rating=f.imdb_rating)
        for f in person.films
    ]
