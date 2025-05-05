from http import HTTPStatus

import pytest

from tests.functional.settings import test_person_settings
from tests.functional.testdata.person_data import (
    generate_persons_data,
    generate_one_person_data,
)


# вывести всех людей
@pytest.mark.parametrize(
    "persons_len, param_data, expected_answer",
    [
        (0, {}, {"status": HTTPStatus.NOT_FOUND}),
        (10, {}, {"status": HTTPStatus.OK, "length": 10}),
        (60, {}, {"status": HTTPStatus.OK, "length": 50}),
        (20, {"page_size": 10}, {"status": HTTPStatus.OK, "length": 10}),
        (60, {"page_number": 3}, {"status": HTTPStatus.NOT_FOUND}),
    ],
)
@pytest.mark.asyncio
async def test_many_persons(
    make_get_request,
    es_write_data,
    persons_len,
    param_data,
    expected_answer,
    es_bulk_query,
):
    es_data = generate_persons_data(persons_len=persons_len)
    bulk_query = es_bulk_query(
        es_data=es_data, es_index=test_person_settings.es_index
    )

    await es_write_data(bulk_query, test_person_settings)
    response = await make_get_request("/api/v1/persons", param_data)

    assert response["status"] == expected_answer["status"]
    if expected_answer["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]


# поиск конкретного человека
@pytest.mark.parametrize(
    "person_id, expected_answer",
    [
        (
            "3e5351d6-4e4a-486b-8529-977672177a07",
            {"status": HTTPStatus.OK},
        ),
        (
            "aaefd58e-4f58-43b6-89ed-e639580bbf78",
            {"status": HTTPStatus.NOT_FOUND},
        ),
    ],
)
@pytest.mark.asyncio
async def test_one_person(
    make_get_request,
    es_write_data,
    person_id,
    expected_answer,
    es_bulk_query,
):
    es_data = generate_one_person_data(
        person_id="3e5351d6-4e4a-486b-8529-977672177a07"
    )
    bulk_query = es_bulk_query(
        es_data=[es_data], es_index=test_person_settings.es_index
    )

    await es_write_data(bulk_query, test_person_settings)
    response = await make_get_request(f"/api/v1/persons/{person_id}")

    assert response["status"] == expected_answer["status"]


# поиск фильмов с участием человека
@pytest.mark.parametrize(
    "person_id, films_len, expected_answer",
    [
        (
            "3e5351d6-4e4a-486b-8529-977672177a07",
            60,
            {"status": HTTPStatus.OK, "length": 60},
        ),
        (
            "3e5351d6-4e4a-486b-8529-977672177a07",
            0,
            {"status": HTTPStatus.OK, "length": 0},
        ),
        (
            "aaefd58e-4f58-43b6-89ed-e639580bbf78",
            10,
            {"status": HTTPStatus.NOT_FOUND},
        ),
    ],
)
@pytest.mark.asyncio
async def test_person_films(
    make_get_request,
    es_write_data,
    person_id,
    films_len,
    expected_answer,
    es_bulk_query,
):
    write_person_id = "3e5351d6-4e4a-486b-8529-977672177a07"
    es_data = generate_one_person_data(
        person_id=write_person_id, films_len=films_len
    )
    bulk_query = es_bulk_query(
        es_data=[es_data], es_index=test_person_settings.es_index
    )

    await es_write_data(bulk_query, test_person_settings)
    response = await make_get_request(f"/api/v1/persons/{person_id}/films")

    assert response["status"] == expected_answer["status"]
    if expected_answer["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]


# поиск с учётом кеша в Redis
@pytest.mark.parametrize(
    "persons_len, param_data, expected_answer",
    [
        (0, {}, {"status": HTTPStatus.NOT_FOUND}),
        (10, {}, {"status": HTTPStatus.OK, "length": 10}),
        (60, {}, {"status": HTTPStatus.OK, "length": 50}),
        (20, {"page_size": 10}, {"status": HTTPStatus.OK, "length": 10}),
        (50 * 11, {"page_number": 11}, {"status": HTTPStatus.NOT_FOUND}),
    ],
)
@pytest.mark.asyncio
async def test_redis(
    make_get_request,
    es_write_data,
    es_delete_data,
    persons_len,
    param_data,
    expected_answer,
    es_bulk_query,
):
    es_data = generate_persons_data(persons_len=persons_len)
    bulk_query = es_bulk_query(
        es_data=es_data, es_index=test_person_settings.es_index
    )

    await es_write_data(bulk_query, test_person_settings)
    response = await make_get_request("/api/v1/persons", param_data)
    await es_delete_data(test_person_settings)
    response = await make_get_request("/api/v1/persons", param_data)

    assert response["status"] == expected_answer["status"]
    if expected_answer["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]


# поиск фильмов с участием человека с учётом кеша в Redis
@pytest.mark.parametrize(
    "person_id, films_len, expected_answer",
    [
        (
            "3e5351d6-4e4a-486b-8529-977672177a07",
            60,
            {"status": HTTPStatus.OK, "length": 60},
        ),
        (
            "3e5351d6-4e4a-486b-8529-977672177a07",
            0,
            {"status": HTTPStatus.OK, "length": 0},
        ),
        (
            "aaefd58e-4f58-43b6-89ed-e639580bbf78",
            10,
            {"status": HTTPStatus.NOT_FOUND},
        ),
    ],
)
@pytest.mark.asyncio
async def test_person_films_redis(
    make_get_request,
    es_write_data,
    es_delete_data,
    person_id,
    films_len,
    expected_answer,
    es_bulk_query,
):
    write_person_id = "3e5351d6-4e4a-486b-8529-977672177a07"
    es_data = generate_one_person_data(
        person_id=write_person_id, films_len=films_len
    )
    bulk_query = es_bulk_query(
        es_data=[es_data], es_index=test_person_settings.es_index
    )

    await es_write_data(bulk_query, test_person_settings)
    response = await make_get_request(f"/api/v1/persons/{person_id}/films")
    await es_delete_data(test_person_settings)
    response = await make_get_request(f"/api/v1/persons/{person_id}/films")

    assert response["status"] == expected_answer["status"]
    if expected_answer["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]
