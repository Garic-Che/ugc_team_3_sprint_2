from typing import Annotated
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query

from services.film import FilmService, get_film_service
from services.bearer import security_jwt
from api.v1.schemes import FilmCommon, PersonCommon, Film
from api.v1.pagination import PaginatedParams

router = APIRouter()


@router.get(
    "/",
    response_model=list[FilmCommon],
    summary="Показ списка фильмов",
)
@router.get(
    "/search",
    response_model=list[FilmCommon],
    summary="Поиск по фильмам",
)
async def films_list(
    genre_id: str = Query(default=None),
    query: str = Query(default=None),
    sort: str = Query(default="-imdb_rating"),
    pagination: PaginatedParams = Depends(),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmCommon]:
    parameters = {
        "genre_id": genre_id,
        "query": query,
        "sort": sort,
        "page_size": pagination.page_size,
        "page_number": pagination.page_number,
    }
    films = await film_service.get_by_parameters(parameters)
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="films not found"
        )

    return [
        FilmCommon(
            uuid=film.id, imdb_rating=film.imdb_rating, title=film.title
        )
        for film in films
    ]


@router.get(
    "/{film_id}", response_model=Film, summary="Полная информация по фильму"
)
async def film_details(
    user: Annotated[dict, Depends(security_jwt)],
    film_id: str,
    film_service: FilmService = Depends(get_film_service),
) -> Film:
    roles = user.get("roles") or []
    film = await film_service.get_by_id(film_id, roles)
    if not film:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="film not found"
        )

    return Film(
        uuid=film.id,
        imdb_rating=film.imdb_rating,
        title=film.title,
        description=film.description,
        genre=[g.model_dump() for g in film.genres],
        directors=[
            PersonCommon(uuid=d.id, full_name=d.full_name)
            for d in film.directors
        ],
        actors=[
            PersonCommon(uuid=a.id, full_name=a.full_name) for a in film.actors
        ],
        writers=[
            PersonCommon(uuid=w.id, full_name=w.full_name)
            for w in film.writers
        ],
    )


# Похожие фильмы. Похожесть можно оценить с помощью ElasticSearch,
# но цель модуля не в этом.
# Сделаем просто: покажем фильмы того же жанра.


@router.get(
    "/{film_id}/similar",
    response_model=list[FilmCommon],
    summary="Похожие фильмы",
)
async def similar_films_list(
    film_id: str,
    pagination: PaginatedParams = Depends(),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmCommon]:
    # Преобразуем параметры в словарь
    parameters = {
        "page_size": pagination.page_size,
        "page_number": pagination.page_number,
    }
    films = await film_service.get_similar_films_by_id(film_id, parameters)
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="films not found"
        )

    return [
        FilmCommon(
            uuid=film.id, imdb_rating=film.imdb_rating, title=film.title
        )
        for film in films
    ]
