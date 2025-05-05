from tests.functional.utils.helpers import User


def generate_user_data(
    id: str = "e46a674b-f608-423b-afc3-f03772875179",
    login: str = "login",
    password: str = "qwery1"
) -> User:
    return User(id=id, login=login, password=password)