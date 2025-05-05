from typing import Any

from state_manager.base_storage import BaseStorage


class StateManager:

    state: dict[str, Any]

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage
        self.state = self.storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        self.state.update({key: value})
        self.storage.save_state(self.state)

    def get_state(self, key: str) -> Any:
        if self.state.__contains__(key):
            return self.state[key]
        return None
