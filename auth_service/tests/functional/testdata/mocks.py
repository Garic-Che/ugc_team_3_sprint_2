from authlib.integrations.starlette_client import OAuthError


class MockOAuth2App:
    def __init__(self, user_info):
        self.user_info = user_info

    async def authorize_access_token(self, request):
        # Проверяем наличие state в сессии
        state = request.session.get("oauth_state")
        if not state:
            raise OAuthError(
                "mismatching_state",
                "CSRF Warning! State not equal in request and response."
            )
        return {"access_token": "mock_token", "userinfo": self.user_info}

    async def parse_id_token(self, request, token):
        return self.user_info
