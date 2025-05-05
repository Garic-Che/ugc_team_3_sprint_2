from http import HTTPStatus
import pytest

from tests.functional.testdata.user_data import generate_user_data
from tests.functional.testdata.mocks import MockOAuth2App
from tests.functional.utils.helpers import get_state_from_session


@pytest.mark.asyncio
async def test_google_auth_new_user(
    make_get_request,
    monkeypatch,
):
    """Тест успешной авторизации нового пользователя через Google."""
    # Создаем мок с данными нового пользователя
    mock_oauth = MockOAuth2App(
        {
            "email": "newuser@google.com",
            "sub": "123456789",
            "name": "New User",
        }
    )
    monkeypatch.setattr(
        "authlib.integrations.starlette_client.StarletteOAuth2App",
        lambda *args, **kwargs: mock_oauth,
    )

    # Сначала делаем запрос на авторизацию
    response = await make_get_request("/api/v1/user/login/google")

    # Получаем state из сессии
    session_cookie = response["cookies"].get("session")
    state = get_state_from_session(session_cookie)
    assert state is not None, "Failed to get state from session"

    # Затем вызываем callback с state из сессии
    response = await make_get_request(
        "/api/v1/user/login/google/callback", cookies={"oauth_state": state}
    )

    assert response["status"] == HTTPStatus.OK
    assert "access_token" in response["cookies"]
    assert "refresh_token" in response["cookies"]


@pytest.mark.asyncio
async def test_google_auth_existing_user(
    make_get_request,
    user_to_db,
    hash_password,
    monkeypatch,
):
    """Тест успешной авторизации существующего пользователя через Google."""
    # Создаем тестового пользователя
    test_email = "existing@google.com"
    user_data = generate_user_data(
        login=test_email,
        password=hash_password("test_password"),
    )
    await user_to_db(user_data)

    # Создаем мок с данными существующего пользователя
    mock_oauth = MockOAuth2App(
        {
            "email": test_email,
            "sub": "123456789",
            "name": "Existing User",
        }
    )
    monkeypatch.setattr(
        "authlib.integrations.starlette_client.StarletteOAuth2App",
        lambda *args, **kwargs: mock_oauth,
    )

    # Сначала делаем запрос на авторизацию
    response = await make_get_request("/api/v1/user/login/google")

    # Получаем state из сессии
    session_cookie = response["cookies"].get("session")
    state = get_state_from_session(session_cookie)
    assert state is not None, "Failed to get state from session"

    # Затем вызываем callback с state из сессии
    response = await make_get_request(
        "/api/v1/user/login/google/callback", cookies={"oauth_state": state}
    )

    assert response["status"] == HTTPStatus.OK
    assert "access_token" in response["cookies"]
    assert "refresh_token" in response["cookies"]


@pytest.mark.asyncio
async def test_google_auth_no_email(
    make_get_request,
    monkeypatch,
):
    """Тест ошибки при отсутствии email от Google."""
    # Создаем мок с данными без email
    mock_oauth = MockOAuth2App(
        {
            "sub": "123456789",
            "name": "User Without Email",
        }
    )
    monkeypatch.setattr(
        "authlib.integrations.starlette_client.StarletteOAuth2App",
        lambda *args, **kwargs: mock_oauth,
    )

    # Сначала делаем запрос на авторизацию
    response = await make_get_request("/api/v1/user/login/google")

    # Получаем state из сессии
    session_cookie = response["cookies"].get("session")
    state = get_state_from_session(session_cookie)
    assert state is not None, "Failed to get state from session"

    # Затем вызываем callback с state из сессии
    response = await make_get_request(
        "/api/v1/user/login/google/callback", cookies={"oauth_state": state}
    )

    assert response["status"] == HTTPStatus.BAD_REQUEST
