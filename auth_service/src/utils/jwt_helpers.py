import jwt
from core.config import settings
from typing import Optional


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token.replace("Bearer ", ""),
            settings.auth_secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except Exception as err:
        return None
