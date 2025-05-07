from http import HTTPStatus

import pytest

from tests.functional.settings import test_genre_settings
from tests.functional.testdata.genre_data import (
    generate_genres_data,
    generate_one_genre_data,
)


# вывести все жанры
@pytest.mark.parametrize(
    "genres_len, param_data, expected_answer",
    [
        # Основные случаи
        (
            0,
            {},
            {"status": HTTPStatus.NOT_FOUND, "detail": "Genres not found"},
        ),  # Нет жанров в базе
        (
            10,
            {},
            {"status": HTTPStatus.OK, "length": 10},
        ),  # 10 жанров, без пагинации
        (
            60,
            {},
            {"status": HTTPStatus.OK, "length": 50},
        ),  # 60 жанров, по умолчанию возвращаем 50
        (
            20,
            {"page_size": 10},
            {"status": HTTPStatus.OK, "length": 10},
        ),  # Пагинация: 20 жанров, запрашиваем 10
        (
            60,
            {"page_number": 3},
            {"status": HTTPStatus.NOT_FOUND, "detail": "Page not found"},
        ),  # Запрашиваем несуществующую страницу
        # Дополнительные случаи
        (
            50,
            {},
            {"status": HTTPStatus.OK, "length": 50},
        ),  # Ровно 50 жанров, без пагинации
        (
            100,
            {"page_size": 20},
            {"status": HTTPStatus.OK, "length": 20},
        ),  # Пагинация: 100 жанров, запрашиваем 20
        (
            100,
            {"page_size": 20, "page_number": 2},
            {"status": HTTPStatus.OK, "length": 20},
        ),  # Пагинация: вторая страница
        (
            100,
            {"page_size": 20, "page_number": 6},
            {"status": HTTPStatus.NOT_FOUND, "detail": "Page not found"},
        ),
        # Запрашиваем несуществующую страницу
        (
            30,
            {"page_size": 40},
            {"status": HTTPStatus.OK, "length": 30},
        ),  # Запрашиваем больше, чем есть
        (
            30,
            {"page_size": 0},
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),
        # Некорректный размер страницы (валидация Pydantic)
        (
            30,
            {"page_size": -1},
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),
        # Некорректный размер страницы (валидация Pydantic)
        (
            30,
            {"page_number": 0},
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),
        # Некорректный номер страницы (валидация Pydantic)
        (
            30,
            {"page_number": -1},
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),
        # Некорректный номер страницы (валидация Pydantic)
        (
            30,
            {"page_size": 10, "page_number": 4},
            {"status": HTTPStatus.NOT_FOUND, "detail": "Page not found"},
        ),
        # Запрашиваем несуществующую страницу
        (
            30,
            {"page_size": 10, "page_number": 3},
            {"status": HTTPStatus.OK, "length": 10},
        ),  # Последняя страница
        (
            30,
            {"page_size": 15, "page_number": 2},
            {"status": HTTPStatus.OK, "length": 15},
        ),  # Ровно две страницы
        (
            30,
            {"page_size": 15, "page_number": 3},
            {"status": HTTPStatus.NOT_FOUND, "detail": "Page not found"},
        ),
        # Запрашиваем несуществующую страницу
        (
            30,
            {"page_size": 30, "page_number": 1},
            {"status": HTTPStatus.OK, "length": 30},
        ),  # Все жанры на одной странице
        (
            30,
            {"page_size": 100, "page_number": 1},
            {"status": HTTPStatus.OK, "length": 30},
        ),  # Запрашиваем больше, чем есть
        (
            30,
            {"page_size": "invalid"},
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),
        # Некорректный тип параметра (валидация Pydantic)
        (
            30,
            {"page_number": "invalid"},
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),
        # Некорректный тип параметра (валидация Pydantic)
        # (
        #     30,
        #     {"unknown_param": 10},
        #     {
        #         "status": HTTPStatus.UNPROCESSABLE_ENTITY,
        #         "detail": "Validation error",
        #     },
        # ),
        # Неизвестный параметр (валидация Pydantic)
    ],
)
class TestAllGenresParametrized:
    @pytest.mark.asyncio
    async def test_many_genres(
        self,
        make_get_request,
        es_write_data,
        genres_len,
        expected_answer,
        param_data,
        redis_clear,
        es_bulk_query,
    ):
        es_data = generate_genres_data(genres_len=genres_len)
        bulk_query = es_bulk_query(
            es_data=es_data, es_index=test_genre_settings.es_index
        )

        await es_write_data(bulk_query, test_genre_settings)
        response = await make_get_request("/api/v1/genres/", param_data)

        assert response["status"] == expected_answer["status"]
        if expected_answer["status"] == HTTPStatus.NOT_FOUND:
            return
        if expected_answer["status"] == HTTPStatus.UNPROCESSABLE_ENTITY:
            return
        assert len(response["body"]) == expected_answer.get("length")

    @pytest.mark.asyncio
    async def test_many_genres_redis(
        self,
        make_get_request,
        es_write_data,
        genres_len,
        expected_answer,
        param_data,
        redis_clear,
        es_delete_data,
        es_bulk_query,
    ):
        es_data = generate_genres_data(genres_len=genres_len)
        bulk_query = es_bulk_query(
            es_data=es_data, es_index=test_genre_settings.es_index
        )

        await es_write_data(bulk_query, test_genre_settings)
        response = await make_get_request("/api/v1/genres/", param_data)
        await es_delete_data(test_genre_settings)
        response = await make_get_request("/api/v1/genres", param_data)

        assert response["status"] == expected_answer["status"]
        if expected_answer["status"] == HTTPStatus.NOT_FOUND:
            return
        if expected_answer["status"] == HTTPStatus.UNPROCESSABLE_ENTITY:
            return
        assert len(response["body"]) == expected_answer["length"]


# поиск конкретного жанра
@pytest.mark.parametrize(
    "genre_id, expected_answer",
    [
        # Корректные UUID
        (
            "3e5351d6-4e4a-486b-8529-977672177a07",
            {
                "status": HTTPStatus.OK,
                "id": "3e5351d6-4e4a-486b-8529-977672177a07",
            },
        ),
        # Жанр найден
        (
            "aaefd58e-4f58-43b6-89ed-e639580bbf78",
            {"status": HTTPStatus.NOT_FOUND, "detail": "Genre not found"},
        ),  # Жанр не найден
        # Некорректные UUID
        (
            "invalid-uuid",
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),  # Некорректный формат UUID
        (
            "123",
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),  # Слишком короткий UUID
        (
            "3e5351d6-4e4a-486b-8529-977672177a07-extra",
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),
        # Слишком длинный UUID
        # (
        #     "",
        #     {
        #         "status": HTTPStatus.UNPROCESSABLE_ENTITY,
        #         "detail": "Validation error",
        #     },
        # ),  # Пустой UUID
        # Крайние случаи
        (
            None,
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),  # None вместо UUID
        (
            12345,
            {
                "status": HTTPStatus.UNPROCESSABLE_ENTITY,
                "detail": "Validation error",
            },
        ),  # Число вместо UUID
        (
            "00000000-0000-0000-0000-000000000000",
            {"status": HTTPStatus.NOT_FOUND, "detail": "Genre not found"},
        ),
        # Нулевой UUID (маловероятно, что такой жанр существует)
    ],
)
class TestOneGenreParametrized:
    @pytest.mark.asyncio
    async def test_one_genre(
        self,
        make_get_request,
        es_write_data,
        redis_clear,
        genre_id,
        expected_answer,
        es_bulk_query,
    ):
        es_data = generate_one_genre_data(
            genre_id="3e5351d6-4e4a-486b-8529-977672177a07"
        )
        bulk_query = es_bulk_query(
            es_data=[es_data], es_index=test_genre_settings.es_index
        )

        await es_write_data(bulk_query, test_genre_settings)
        response = await make_get_request(f"/api/v1/genres/{genre_id}")

        assert response["status"] == expected_answer["status"]

    @pytest.mark.asyncio
    async def test_one_genre_redis(
        self,
        make_get_request,
        es_write_data,
        redis_clear,
        genre_id,
        expected_answer,
        es_delete_data,
        es_bulk_query,
    ):
        es_data = generate_one_genre_data(
            genre_id="3e5351d6-4e4a-486b-8529-977672177a07"
        )
        bulk_query = es_bulk_query(
            es_data=[es_data], es_index=test_genre_settings.es_index
        )

        await es_write_data(bulk_query, test_genre_settings)
        response = await make_get_request(f"/api/v1/genres/{genre_id}")
        await es_delete_data(test_genre_settings)
        response = await make_get_request(f"/api/v1/genres/{genre_id}")

        assert response["status"] == expected_answer["status"]
