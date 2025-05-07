from http import HTTPStatus

import pytest

from tests.functional.testdata.user_data import generate_user_data


# вход пользователя
@pytest.mark.parametrize(
    "login, password, expected_answer",
    [
        ("who", "cares", HTTPStatus.OK),
        ("cares", "who", HTTPStatus.NOT_FOUND),
        ("login", "password", HTTPStatus.NOT_FOUND),
    ],
)
@pytest.mark.asyncio
async def test_login_user(
    make_post_request,
    user_to_db,
    hash_password,
    login,
    password,
    expected_answer,
):
    user_data_to_db = generate_user_data(
        login="who", password=hash_password("cares")
    )

    await user_to_db(user_data_to_db)
    response = await make_post_request(
        "/api/v1/user/login",
        {"login": login, "password": password},
    )

    assert response["status"] == expected_answer


# профиль пользователя
@pytest.mark.parametrize(
    "id, login, expected_answer",
    [
        ("b56a5a1c-ebc0-4a27-a0d5-42a9876933f3", "login", HTTPStatus.OK),
    ],
)
@pytest.mark.asyncio
async def test_user_profile(
    make_post_request,
    make_get_request,
    user_to_db,
    hash_password,
    id,
    login,
    expected_answer,
):
    db_user_id = "b56a5a1c-ebc0-4a27-a0d5-42a9876933f3"
    db_login = "login"
    db_password = "qwerty1"
    user_data_to_db = generate_user_data(
        id=db_user_id, login=db_login, password=hash_password(db_password)
    )

    await user_to_db(user_data_to_db)
    login_response = await make_post_request(
        "/api/v1/user/login",
        {"login": db_login, "password": db_password},
    )
    response = await make_get_request(
        "/api/v1/user/", cookies=login_response["cookies"]
    )

    assert response["status"] == expected_answer
    if expected_answer != HTTPStatus.OK:
        return
    assert response["body"]["id"] == id
    assert response["body"]["login"] == login


@pytest.mark.parametrize(
    "test_case, expected_status",
    [
        ("valid_refresh", HTTPStatus.OK),
        ("invalid_refresh", HTTPStatus.NOT_FOUND),
        ("missing_refresh", HTTPStatus.NOT_FOUND),
    ],
)
@pytest.mark.asyncio
async def test_refresh_token(
    make_post_request,
    user_to_db,
    hash_password,
    test_case,
    expected_status,
):
    # 1. Создаем тестового пользователя и логинимся
    user_data = generate_user_data(
        login="test_user", password=hash_password("test_pass")
    )
    await user_to_db(user_data)

    login_response = await make_post_request(
        "/api/v1/user/login", {"login": "test_user", "password": "test_pass"}
    )

    # 2. Подготавливаем данные для теста в зависимости от случая
    if test_case == "valid_refresh":
        cookies = login_response["cookies"]
    elif test_case == "invalid_refresh":
        cookies = {"refresh_token": "invalid_token"}
    else:  # missing_refresh
        cookies = {}

    # 3. Отправляем запрос на обновление токена
    response = await make_post_request(
        "/api/v1/user/update_access", cookies=cookies
    )

    # 4. Проверяем результат
    assert response["status"] == expected_status

    # Дополнительные проверки для успешного случая
    if test_case == "valid_refresh":
        assert "access_token" in response["cookies"]
        assert "refresh_token" in response["cookies"]
        assert (
            response["cookies"]["access_token"]
            != login_response["cookies"]["access_token"]
        )
        assert (
            response["cookies"]["refresh_token"]
            != login_response["cookies"]["refresh_token"]
        )


@pytest.mark.asyncio
async def test_history_with_simple_pagination(
    make_post_request, make_get_request, user_to_db, hash_password
):
    # 1. Создаем тестового пользователя и логинимся
    user_data = generate_user_data(
        login="test_user", password=hash_password("test_pass")
    )
    await user_to_db(user_data)

    # Создаем 15 записей в истории
    [
        await make_post_request(
            "/api/v1/user/login",
            {"login": "test_user", "password": "test_pass"},
        )
        for _ in range(15)
    ]

    login_response = await make_post_request(
        "/api/v1/user/login", {"login": "test_user", "password": "test_pass"}
    )

    # Тестируем первую страницу
    response_page1 = await make_get_request(
        "/api/v1/user/history",
        cookies=login_response["cookies"],
        params={"page": 1, "per_page": 5},
    )

    assert response_page1["status"] == HTTPStatus.OK
    assert len(response_page1["body"]) == 5
    assert isinstance(response_page1["body"], list)
    assert "user_agent" in response_page1["body"][0]
    assert "timestamp" in response_page1["body"][0]

    # Тестируем вторую страницу
    response_page2 = await make_get_request(
        "/api/v1/user/history",
        cookies=login_response["cookies"],
        params={"page": 2, "per_page": 5},
    )

    assert response_page2["status"] == HTTPStatus.OK
    assert len(response_page2["body"]) == 5


@pytest.mark.parametrize(
    "login, password, expected_answer",
    [
        ("newuser1", "securepass", HTTPStatus.OK),
        ("existing_user", "secure_pass", HTTPStatus.CONFLICT),
    ],
)
@pytest.mark.asyncio
async def test_register_user(
    make_post_request,
    user_to_db,
    hash_password,
    login,
    password,
    expected_answer,
):
    user_data_to_db = generate_user_data(
        login="existing_user", password=hash_password("secure_pass")
    )

    await user_to_db(user_data_to_db)
    response = await make_post_request(
        "/api/v1/user/register",
        {"login": login, "password": password},
    )

    assert response["status"] == expected_answer


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "login, expected_answer",
    [
        ("some_user", HTTPStatus.OK),
        ("", HTTPStatus.UNPROCESSABLE_ENTITY),
        ("two", HTTPStatus.UNPROCESSABLE_ENTITY),
    ],
    ids=["seccess", "no_validate_login", "no _validate_len_login"],
)
async def test_change_login(
    user_to_db,
    make_post_request,
    make_put_request,
    hash_password,
    login,
    expected_answer,
):
    user_data_to_db = generate_user_data(
        login="test_user", password=hash_password("password")
    )

    await user_to_db(user_data_to_db)

    login_response = await make_post_request(
        "/api/v1/user/login", {"login": "test_user", "password": "password"}
    )

    response = await make_put_request(
        "/api/v1/user/change/login",
        {
            "new_login": login,
        },
        cookies=login_response["cookies"],
    )
    assert response["status"] == expected_answer


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "password, exist_cookies, expected_answer",
    [
        ("new_password", True, HTTPStatus.OK),
        ("new_password", False, HTTPStatus.UNAUTHORIZED),
        ("", False, HTTPStatus.UNAUTHORIZED),
        ("no_match_password", False, HTTPStatus.UNAUTHORIZED),
    ],
    ids=[
        "have_token",
        "no_token",
        "no_validate_password_len",
        "no_match_password",
    ],
)
async def test_change_password(
    user_to_db,
    make_post_request,
    make_put_request,
    hash_password,
    password,
    exist_cookies,
    expected_answer,
):
    user_data_to_db = generate_user_data(
        login="test_user", password=hash_password("password")
    )

    await user_to_db(user_data_to_db)

    login_response = await make_post_request(
        "/api/v1/user/login", {"login": "test_user", "password": "password"}
    )

    response = await make_put_request(
        "/api/v1/user/change/password",
        {
            "old_password": "password"
            if "no_match_password" != password
            else password,
            "new_password": password,
        },
        cookies=login_response["cookies"] if exist_cookies else None,
    )
    assert response["status"] == expected_answer
