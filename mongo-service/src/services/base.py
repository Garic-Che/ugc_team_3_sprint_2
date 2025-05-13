from uuid import UUID
from typing import TypeVar, Generic, Type, Iterable
from abc import ABC, abstractmethod
from datetime import datetime

from beanie import UpdateResponse
from beanie.operators import In 
from pymongo.errors import BulkWriteError, DuplicateKeyError

from .models import UpdateModel
from models.entities import Entity
from exceptions.services import DuplicateError, NotFoundKeyError


TDocument = TypeVar("TDocument", bound=Entity)
TUpdateModel = TypeVar("TUpdateModel", bound=UpdateModel)


class CRUDServiceABC(ABC, Generic[TDocument, TUpdateModel]):
    @abstractmethod
    async def insert(self, entities: list[TDocument]) -> list[TDocument]:
        pass
    
    @abstractmethod
    async def update(self, entity_update: TUpdateModel) -> TDocument:
        pass

    @abstractmethod
    async def delete(self, ids: list[UUID]) -> list[UUID]:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: UUID) -> list[TDocument]:
        pass

    @abstractmethod
    async def get_by_timerange(self, start: datetime, end: datetime) -> list[TDocument]:
        pass

    @abstractmethod
    async def get_by_content_id(self, content_id: UUID) -> list[TDocument]:
        pass


class MongoCRUDMixin(Generic[TDocument, TUpdateModel]):
    def __init__(self, model: Type[TDocument]):
        self.model = model 

    async def insert(self, entities: list[TDocument]) -> list[TDocument]:
        try:
            await self.model.insert_many(entities)
            return entities
        except BulkWriteError as bwe:
            write_errors = bwe.details.get("writeErrors", [])
            for error in write_errors:
                if error.get("code") == 11000:
                    collection_name = self.model.__class__.__name__
                    raise DuplicateError(collection_name)
            raise bwe
        
    async def delete(self, ids: list[UUID]) -> list[UUID]:
        nonexistent_ids = await self._get_nonexistent_ids(ids)
        if nonexistent_ids:
            raise NotFoundKeyError(nonexistent_ids)
        await self.model.find_many(In(self.model.id, ids)).delete_many()
        return ids

    async def _get_nonexistent_ids(self, ids: list[UUID]) -> Iterable[UUID]:
        existing_entities = await self.model.find_many(In(self.model.id, ids)).to_list()
        if len(existing_entities) == len(ids):
            return []
        existing_ids = [entity.id for entity in existing_entities]
        nonexistent_ids = set(ids).difference(existing_ids)
        return nonexistent_ids

    async def update(self, entity_update: TUpdateModel) -> TDocument:
        try:
            entity = await self.model.get(entity_update.id)
            if not entity:
                raise NotFoundKeyError([entity_update.id])
            update_mapping = entity_update.model_dump(exclude_unset=True)
            updated_document = (await self.model.find_one(self.model.id == entity_update.id)
                                .update_one({"$set": update_mapping}, response_type=UpdateResponse.NEW_DOCUMENT))
            return self.model(**updated_document.model_dump())
        except DuplicateKeyError:
            collection_name = self.model.__name__
            raise DuplicateError(collection_name)
        
    async def get_by_user(self, user_id: UUID) -> list[TDocument]:
        user_entities = await self.model.find(self.model.user_id == user_id).to_list()
        if not user_entities:
            return []
        return user_entities

    async def get_by_timerange(self, start: datetime, end: datetime) -> list[TDocument]:
        timerange_entities = await self.model.find(self.model.created_at >= start, self.model.created_at < end).to_list()
        if not timerange_entities:
            return []
        return timerange_entities
    
    async def get_by_content_id(self, content_id: UUID) -> list[TDocument]:
        content_entities = await self.model.find(self.model.content_id == content_id).to_list()
        if not content_entities:
            return []
        return content_entities