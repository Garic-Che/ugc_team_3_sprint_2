from http import HTTPStatus
from functools import wraps

from flask import request, jsonify

from core.config import settings


def internal_auth_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # Проверка заголовка авторизации
        auth_header = request.headers.get("X-Internal-Auth")

        if not auth_header:
            return jsonify(
                {"message": "Authentication required"}
            ), HTTPStatus.UNAUTHORIZED

        # TODO: Нужно ли шифровать?
        if not auth_header == settings.ugc_api_secret_key:
            return jsonify(
                {"message": "Invalid authentication"}
            ), HTTPStatus.FORBIDDEN

        return func(*args, **kwargs)

    return decorated_function
