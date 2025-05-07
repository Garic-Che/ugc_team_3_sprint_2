import http
import json
from enum import Enum
from jose import JWTError, jwt

import requests
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class Roles(str, Enum):
    ADMIN = "ADMIN"
    SUPERUSER = "SUPERUSER"
    SUBSCRIBER = "SUBSCRIBER"


class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Сначала пробуем стандартную аутентификацию Django
        if username and password:
            try:
                user = User.objects.get(login=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                pass

        # Если не сработало - пробуем через auth_service
        url = settings.AUTH_API_LOGIN_URL
        payload = {"login": username, "password": password}
        response = requests.post(url, data=json.dumps(payload))
        if response.status_code != http.HTTPStatus.OK:
            return None

        # data = response.json()
        # Получаем access токен из куки
        access_token = response.cookies.get("access_token")
        if not access_token:
            return None

        # request.session["access_token"] = access_token
        try:
            payload = jwt.decode(
                access_token, settings.JWT_SECRET_KEY, algorithms=["HS256"]
            )
            user_id = payload.get("user_id")
            roles = payload.get("roles") or []
            print("roles:", roles)
        except JWTError:
            return None

        try:
            user, created = User.objects.get_or_create(
                id=user_id,
            )
            user.login = username
            user.is_staff = any(
                role in roles for role in [Roles.ADMIN, Roles.SUPERUSER]
            )
            user.is_active = True

            user.save()
        except Exception:
            return None

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
