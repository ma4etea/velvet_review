from src.adapters.redis_adapter import RedisAdapter
from src.repositories.cache.auths import AuthsRepository
from src.repositories.cache.users import UsersRepository
from types import TracebackType


class CacheManager:
    def __init__(self, adapter: RedisAdapter):
        self.adapter = adapter

    async def __aenter__(self):
        self.auths = AuthsRepository(self.adapter)
        self.users = UsersRepository(self.adapter)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.adapter.rollback()

    async def commit(self):
        await self.adapter.commit()

    async def rollback(self):
        await self.adapter.rollback()
