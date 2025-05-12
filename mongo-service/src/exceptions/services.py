from uuid import UUID


class DuplicateError(Exception):
    def __init__(self, collection: str):
        super().__init__(f"Unique constraint in {collection} is violated")
        self.collection = collection


class NotFoundKeyError(Exception):
    def __init__(self, not_found_keys: list[UUID]):
        super().__init__(f"The following keys were not found: {not_found_keys}")
        self.not_found_keys = not_found_keys
