from typing import Generic

from src.adapters.redis_adapter import RedisAdapter
from src.exceptions.base import ObjectAlreadyExistsException
from src.repositories.cache.mappers.base import DataMapper, SchemaType


class BaseRepository(Generic[SchemaType]):
    mapper: type[DataMapper[SchemaType]]
    space_name: str

    def __init__(self, adapter: RedisAdapter):
        self.adapter = adapter

    def get_space_name(self, obj_id: str) -> str:
        return f"{self.space_name}{obj_id}"

    async def get_one_or_none(self, obj_id: str) -> SchemaType | None:
        result = await self.adapter.get_one_or_none(key=self.get_space_name(obj_id))
        if result is None:
            return None
        return self.mapper.to_domain(result)

    async def add(
        self, dto: SchemaType, obj_id: str, ttl: int | None = None, forced: bool = True
    ) -> SchemaType:
        """
        forced = True: создает(перезаписывает) dto, даже если уже существует
        :raise ObjectAlreadyExistsException: При forced = False, Если dto уже существует.
        """
        success = await self.adapter.set(
            key=self.get_space_name(obj_id),
            value=self.mapper.to_cache(dto),
            ttl=ttl,
            forced=forced,
        )
        if not success and not forced:
            raise ObjectAlreadyExistsException
        return dto

    async def delete(self, obj_id: str) -> None:
        await self.adapter.delete_one(key=self.get_space_name(obj_id))
