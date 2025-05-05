import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query

from services.genre import GenreService, get_genre_service
from api.v1.schemes import FilmCommon, GenreCommon, Genre
from api.v1.pagination import PaginatedParams

router = APIRouter()


@router.get(
    "/",
    response_model=list[GenreCommon],
    summary="Показ списка жанров",
)
@router.get(
    "/search",
    response_model=list[GenreCommon],
    summary="Поиск по жанрам",
)
async def genres_list(
    query: str = Query(default=None, description="Поиск по названию жанра"),
    pagination: PaginatedParams = Depends(),
    genre_service: GenreService = Depends(get_genre_service),
) -> list[GenreCommon]:
    parameters = {
        "query": query,  # Поиск по имени жанра
        "page_size": pagination.page_size,
        "page_number": pagination.page_number,
    }
    genres = await genre_service.get_by_parameters(parameters)
    if not genres:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Genres not found"
        )

    # Возвращаем список жанров, теперь без поля 'description'
    return [
        GenreCommon(uuid=genre.uuid, name=genre.name)  # Без description
        for genre in genres
    ]


@router.get(
    "/{genre_id}",
    response_model=Genre,
    summary="Данные по конкретному жанру с фильмами",
)
async def genre_details(
    genre_id: uuid.UUID,
    pagination: PaginatedParams = Depends(),
    sort: str = Query("-imdb_rating", description="Сортировка по imdb_rating"),
    genre_service: GenreService = Depends(get_genre_service),
) -> Genre:
    """Получаем жанр и связанные с ним фильмы
    с параметрами пагинации и сортировки."""

    # Параметры пагинации и сортировки
    parameters = {
        "page_size": pagination.page_size,
        "page_number": pagination.page_number,
        "sort": sort,
    }

    # Получаем жанр с фильмами, передавая параметры
    genre = await genre_service.get_by_id(genre_id, parameters)

    if not genre:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Genre not found"
        )

    return Genre(
        uuid=genre.uuid,
        name=genre.name,
        films=[
            FilmCommon(uuid=f.id, imdb_rating=f.imdb_rating, title=f.title)
            for f in genre.films
        ],
    )
