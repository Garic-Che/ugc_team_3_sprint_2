"""функциональные тесты для метода /film"""

from http import HTTPStatus

import pytest

from tests.functional.settings import test_film_settings
from tests.functional.testdata.movie_data import (
    generate_movies_data,
    generate_one_movie_data,
)


# вывести все фильмы
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "movies_len, param_data, expected_answer",
    [
        (0, {}, {"status": HTTPStatus.NOT_FOUND}),
        (10, {}, {"status": HTTPStatus.OK, "length": 10}),
        (60, {}, {"status": HTTPStatus.OK, "length": 50}),
        (20, {"page_size": 10}, {"status": HTTPStatus.OK, "length": 10}),
        (60, {"page_number": 3}, {"status": HTTPStatus.NOT_FOUND}),
    ],
)
async def test_show_all_films(
    make_get_request,
    es_write_data,
    es_bulk_query,
    movies_len,
    param_data,
    expected_answer,
):
    es_data = generate_movies_data(movies_len=movies_len)
    bulk_query = es_bulk_query(
        es_data=es_data, es_index=test_film_settings.es_index
    )

    await es_write_data(bulk_query, test_film_settings)
    response = await make_get_request("/api/v1/films", param_data)

    assert response["status"] == expected_answer["status"]
    if expected_answer["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]


# поиск конкретного фильма
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "movie_id, expected_status",
    [
        ("3e5351d6-4e4a-486b-8529-977672177a07", HTTPStatus.OK),
        ("aaefd58e-4f58-43b6-89ed-e639580bbf78", HTTPStatus.NOT_FOUND),
    ],
    ids=["film exist", "film not exist"],
)
async def test_one_film(
    make_get_request,
    es_bulk_query,
    es_write_data,
    movie_id,
    expected_status,
):
    es_data = generate_one_movie_data(
        movie_id="3e5351d6-4e4a-486b-8529-977672177a07"
    )
    bulk_query = es_bulk_query(
        es_data=[es_data], es_index=test_film_settings.es_index
    )

    await es_write_data(bulk_query, test_film_settings)
    response = await make_get_request(f"/api/v1/films/{movie_id}")

    assert response["status"] == expected_status


# поиск с учётом кеша в Redis
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "movies_len, param_data, expected_answer",
    [
        (0, {}, {"status": HTTPStatus.NOT_FOUND}),
        (10, {}, {"status": HTTPStatus.OK, "length": 10}),
        (60, {}, {"status": HTTPStatus.OK, "length": 50}),
        (20, {"page_size": 10}, {"status": HTTPStatus.OK, "length": 10}),
        (50 * 11, {"page_number": 11}, {"status": HTTPStatus.NOT_FOUND}),
    ],
)
async def test_cache_all_film(
    make_get_request,
    es_write_data,
    es_delete_data,
    es_bulk_query,
    redis_clear,
    movies_len,
    param_data,
    expected_answer,
):
    es_data = generate_movies_data(movies_len=movies_len)
    bulk_query = es_bulk_query(
        es_data=es_data, es_index=test_film_settings.es_index
    )

    await es_write_data(bulk_query, test_film_settings)
    response = await make_get_request("/api/v1/films", param_data)
    await es_delete_data(test_film_settings)
    response = await make_get_request("/api/v1/films", param_data)

    assert response["status"] == expected_answer["status"]
    if expected_answer["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]
