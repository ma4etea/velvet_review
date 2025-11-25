from typing import cast

from redis.asyncio import Redis

from src.adapters.custom_redis import CustomRedis, CustomPipeline
from src.config import settings
from src.logging_config import logger


def create_redis_client(host: str, port: int, db: int = 0):
    """
    decode_responses=True Автоматические превращает байты в строки на выходе
    """
    return CustomRedis(host=host, port=port, db=db, decode_responses=True)


redis_client = create_redis_client(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


class RedisAdapter:
    def __init__(self, redis: CustomRedis):
        self.redis = redis
        self.pending_keys: list[str] = []
        self.deleting_keys: list[str] = []

    async def set(
        self, key: str, value: str = "", ttl: int | None = None, forced: bool = True
    ) -> bool:
        if not forced:
            if await self.check_one(key):
                return False
        pending_key = f"pending:{key}"
        self.pending_keys.append(pending_key)
        result = await self.redis.set(name=pending_key, value=value, ex=ttl)
        return result

    async def get_one_or_none(self, key: str) -> str | None:
        return await self.redis.get(name=key)

    async def get_ttl(self, key: str) -> int:
        return await self.redis.ttl(key)

    async def delete_one(self, key: str) -> None:
        self.deleting_keys.append(key)

    async def check_one(self, key: str) -> bool:
        return await self.redis.exists(key) == 1

    async def add_ids_to_list(self, list_key_name: str, *ids: str, ttl: int | None = None) -> int:
        """
        :param list_key_name: ключ списка
        :param ids: id элемента для добавления в список
        :param ttl: время жизни списка если нужно
        :return: количество элементов в списке
        """
        length = await self.redis.lpush(list_key_name, *ids)
        if ttl:
            await self.redis.expire(name=list_key_name, time=ttl)
        return length

    async def get_ids_from_list(self, list_key_name: str) -> list[str]:
        """
        :param list_key_name: ключ списка
        :return: все ids из списка
        """
        ids = await self.redis.lrange(name=list_key_name, start=0, end=-1)
        return ids

    async def commit(self):
        if self.pending_keys:
            pipeline = self._remove_prefix_bulk(*self.pending_keys, prefix="pending:")
            await pipeline.execute()
            self.pending_keys.clear()

        if self.deleting_keys:
            await self.redis.delete(*self.deleting_keys)
            self.deleting_keys.clear()

    async def rollback(self):
        """удаляет все ключи с пометкой pending из этой транзакции"""
        if self.pending_keys:
            await self.redis.delete(*self.pending_keys)

        if self.deleting_keys:
            self.deleting_keys.clear()

    async def close(self):
        if self.redis:
            await self.redis.aclose()
            logger.info("❎ Redis: Соединение закрыто.")

    def _remove_prefix_bulk(self, *keys: str, prefix: str) -> CustomPipeline:
        """Убирает префикс ключей из списка"""
        pipeline = self.redis.pipeline()
        for key in keys:
            pipeline.rename(key, key.removeprefix(prefix))
        return pipeline

    async def get_all(self, *keys: str) -> list[str]:
        pipeline = self.redis.pipeline()
        for key in keys:
            pipeline.get(key)

        result: list[str] = await pipeline.execute()
        return result


redis_adapter = RedisAdapter(redis_client)
redis_for_fastapi_cache = cast(Redis, redis_client)
