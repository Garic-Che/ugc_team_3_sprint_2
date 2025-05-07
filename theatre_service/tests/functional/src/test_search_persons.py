from http import HTTPStatus

import pytest

from tests.functional.settings import test_person_settings
from tests.functional.testdata.person_data import (
    generate_persons_data,
    generate_one_person_data,
)


# тест N персон и граничных случаев по валидации данных
@pytest.mark.parametrize(
    "persons_len, param_data, expected_answer",
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
async def test_search_many_persons(
    make_get_request,
    es_write_data,
    redis_clear,
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
    if response["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]


# Тест на поиск конкретной персоны
@pytest.mark.parametrize(
    "param_data, expected_answer",
    [
        ({"query": "Otus59"}, {"status": HTTPStatus.OK, "length": 1}),
        ({"query": "Otus58"}, {"status": HTTPStatus.OK, "length": 1}),
        ({"query": "Nonexistent"}, {"status": HTTPStatus.NOT_FOUND}),
        ({"query": ""}, {"status": HTTPStatus.OK, "length": 50}),
    ],
)
@pytest.mark.asyncio
async def test_search_one_person(
    make_get_request,
    es_write_data,
    redis_clear,
    param_data,
    expected_answer,
    es_bulk_query,
):
    es_data = generate_persons_data(persons_len=60)
    bulk_query = es_bulk_query(
        es_data=es_data, es_index=test_person_settings.es_index
    )

    await es_write_data(bulk_query, test_person_settings)
    response = await make_get_request("/api/v1/persons", param_data)

    assert response["status"] == expected_answer["status"]
    if response["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]


# поиск персон с участием человека с учётом кеша в Redis
@pytest.mark.parametrize(
    "param_data, expected_answer",
    [
        (
            {"query": "Matthew McConaughey"},
            {"status": HTTPStatus.OK, "length": 1},
        ),
        ({"query": "Nonexistent"}, {"status": HTTPStatus.NOT_FOUND}),
    ],
)
@pytest.mark.asyncio
async def test_search_person_redis(
    make_get_request,
    es_write_data,
    redis_clear,
    es_delete_data,
    param_data,
    expected_answer,
    es_bulk_query,
):
    write_person_name = "Matthew McConaughey"
    es_data = generate_one_person_data(person_name=write_person_name)
    bulk_query = es_bulk_query(
        es_data=[es_data], es_index=test_person_settings.es_index
    )

    await es_write_data(bulk_query, test_person_settings)
    response = await make_get_request("/api/v1/persons", param_data)
    await es_delete_data(test_person_settings)
    response = await make_get_request("/api/v1/persons", param_data)

    assert response["status"] == expected_answer["status"]
    if response["status"] == HTTPStatus.NOT_FOUND:
        return
    assert len(response["body"]) == expected_answer["length"]
