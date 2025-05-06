import abc
from typing import Any


class BaseStorage(abc.ABC):
    @abc.abstractmethod
    def save_state(self, state: dict[str, Any]) -> None:
        ...

    @abc.abstractmethod
    def retrieve_state(self) -> dict[str, Any]:
        ...

