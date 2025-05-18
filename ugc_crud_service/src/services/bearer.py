import http
from typing import Optional

from jose import jwt
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings


def decode_token(token: str) -> Optional[dict]:
    """
    Функция декодирует токен, используя секретный ключ,
    сохранённый в объекте settings в поле jwt_secret_key.
    Возвращает содержимое токена в виде словаря или None,
    если токен невалиден или при декодировании
    было выброшено исключение.
    """
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception:
        return None


class JWTBearer(HTTPBearer):
    """
    Класс - наследник fastapi.security.HTTPBearer.
    Рекомендуем исследовать этот класс.
    Метод `__call__` класса HTTPBearer возвращает объект
    HTTPAuthorizationCredentials из заголовка `Authorization`

    class HTTPAuthorizationCredentials(BaseModel):
        scheme: str #  'Bearer'
        credentials: str #  сам токен в кодировке Base64

    FastAPI при использовании класса HTTPBearer добавит
    всё необходимое для авторизации в Swagger документацию.
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        """
        Переопределение метода родительского класса HTTPBearer.
        Логика проста: достаём токен из заголовка и декодируем его.
        В результате возвращаем словарь из payload токена или выбрасываем исключение.
        Так как далее объект этого класса будет использоваться как зависимость Depends(...),
        то при этом будет вызван метод `__call__`.
        """
        credentials: HTTPAuthorizationCredentials = await super().__call__(
            request
        )
        if not credentials:
            raise HTTPException(
                status_code=http.HTTPStatus.FORBIDDEN,
                detail="Invalid authorization code.",
            )
        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail="Only Bearer token might be accepted",
            )
        decoded_token = self.parse_token(credentials.credentials)
        if not decoded_token:
            raise HTTPException(
                status_code=http.HTTPStatus.FORBIDDEN,
                detail="Invalid or expired token.",
            )
        return decoded_token

    @staticmethod
    def parse_token(jwt_token: str) -> Optional[dict]:
        return decode_token(jwt_token)


security_jwt = JWTBearer()
