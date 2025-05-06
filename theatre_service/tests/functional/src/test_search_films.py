from http import HTTPStatus

import pytest

from tests.functional.settings import test_film_settings
from tests.functional.testdata.movie_data import (
    generate_movies_data,
    generate_one_movie_data,
)


# тест N фильмов и граничных случаев по валидации данных
@pytest.mark.parametrize(
    "movies_len, param_data, expected_answer",
    [
        (0, {"query": ""}, {"status": HTTPStatus.NOT_FOUND}),
        (10, {"query": ""}, {"status": HTTPStatus.OK, "length": 10}),
        (60, {"query": ""}, {"status": HTTPStatus.OK, "length": 50}),
        (
            20,
            {"page_size": 10, "query": ""},
            {"status": HTTPStatus.OK, "length": 10},
        ),
        (
            60,
            {"page_number": 3, "query": ""},
            {"status": HTTPStatus.NOT_FOUND},
        ),
    ],
)
@pytest.mark.asyncio
async def test_search_many_movies(
    make_get_request,
    es_write_data,
    redis_clear,
    movies_len,
    param_data,
    expected_answer,
    es_bulk_query,
):
    es_data = generate_movies_data(movies_len=movies_len)
    bulk_query = es_bulk_query(
        es_data=es_data, es_index=test_film_settings.es_index
    )

    await es_write_data(bulk_query, test_film_settings)
    response = await make_get_request("/api/v1/films", param_data)

    assert response["status"] == expected_answer["status"]
    if response["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]


# Тест на поиск конкретного фильма
@pytest.mark.parametrize(
    "param_data, expected_answer",
    [
        ({"query": "Movie59"}, {"status": HTTPStatus.OK, "length": 1}),
        ({"query": "Movie58"}, {"status": HTTPStatus.OK, "length": 1}),
        ({"query": "Nonexistent"}, {"status": HTTPStatus.NOT_FOUND}),
        ({"query": ""}, {"status": HTTPStatus.OK, "length": 50}),
    ],
)
@pytest.mark.asyncio
async def test_search_one_movies(
    make_get_request,
    es_write_data,
    redis_clear,
    param_data,
    expected_answer,
    es_bulk_query,
):
    es_data = generate_movies_data(
        movies_len=60
    )  # Generating a set of 60 movies
    bulk_query = es_bulk_query(
        es_data=es_data, es_index=test_film_settings.es_index
    )

    await es_write_data(bulk_query, test_film_settings)
    response = await make_get_request("/api/v1/films", param_data)

    assert response["status"] == expected_answer["status"]
    if response["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]


# поиск фильмов с участием человека с учётом кеша в Redis
@pytest.mark.parametrize(
    "param_data, expected_answer",
    [
        ({"query": "The Lion King"}, {"status": HTTPStatus.OK, "length": 1}),
        ({"query": "Nonexistent"}, {"status": HTTPStatus.NOT_FOUND}),
    ],
)
@pytest.mark.asyncio
async def test_search_movies_redis(
    make_get_request,
    es_write_data,
    redis_clear,
    es_delete_data,
    param_data,
    expected_answer,
    es_bulk_query,
):
    write_movie_title = "The Lion King"
    es_data = generate_one_movie_data(movie_title=write_movie_title)
    bulk_query = es_bulk_query(
        es_data=[es_data], es_index=test_film_settings.es_index
    )

    await es_write_data(bulk_query, test_film_settings)
    response = await make_get_request("/api/v1/films", param_data)
    await es_delete_data(test_film_settings)
    response = await make_get_request("/api/v1/films", param_data)

    assert response["status"] == expected_answer["status"]
    if response["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]
