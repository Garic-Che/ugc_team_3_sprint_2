from typing import Dict, Any
from http import HTTPStatus

import aiohttp


def make_cache_key(
    key: str,
    params: Dict[str, Any],
) -> str:
    """Создание ключа для CacheStorage по первоначальному ключу
    с добавленными к нему параметрами"""
    params_to_key = []
    for param in params:
        params_to_key.append(f"{param}={params[param]}")

    return key + "?" + "&".join(params_to_key)


async def check_access(accesses: list[str], roles: list[str] = []) -> str:
    """Проверка пользователя на доступ к контенту"""
    if not accesses:
        return True

    for access in accesses:
        for role in roles:
            if access == role["name"]:
                return True

    return False


async def make_get_request(url: str, parameters: dict[str, Any] = {}):
    body = {}
    status = HTTPStatus.BAD_GATEWAY
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=parameters, timeout=10
            ) as response:
                body = await response.json()
                status = response.status
    finally:
        return {"body": body, "status": status}
