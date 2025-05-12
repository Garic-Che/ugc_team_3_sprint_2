from uuid import UUID
from typing import Iterable


class DuplicateError(Exception):
    def __init__(self, collection: str):
        super().__init__(f"Unique constraint in {collection} is violated")
        self.collection = collection


class NotFoundKeyError(Exception):
    def __init__(self, not_found_keys: Iterable[UUID]):
        key_str = ','.join([str(key) for key in not_found_keys])
        super().__init__(f"The following keys were not found: {key_str}")
        self.not_found_keys = not_found_keys
