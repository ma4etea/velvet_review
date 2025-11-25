from contextlib import asynccontextmanager

from src.adapters.s3_adapter import S3Adapter, get_s3_client
from src.repositories.s3.unit_images import UnitImagesRepository
from types import TracebackType


class S3Manager:
    def __init__(self, adapter: S3Adapter):
        self.adapter = adapter

    async def __aenter__(self):
        self.unit_images = UnitImagesRepository(self.adapter)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.adapter.rollback()
        await self.adapter.close()

    async def commit(self):
        await self.adapter.commit()

    async def rollback(self):
        await self.adapter.rollback()


# @asynccontextmanager
# async def get_s3_manager():
#     async for s3_client in get_s3_client():
#         s3_adapter = S3Adapter(s3_client)
#         async with S3Manager(s3_adapter) as s3_manager:
#             yield s3_manager


@asynccontextmanager
async def get_s3_manager_fabric():
    async with get_s3_client() as s3_client:
        s3_adapter = S3Adapter(s3_client)
        async with S3Manager(s3_adapter) as s3_manager:
            yield s3_manager


# class S3Manager:
#     def __init__(self, adapter_cls: type, client_factory):
#         """
#         adapter_cls — класс адаптера, который принимает S3 client
#         client_cm — async context manager S3 клиента (aioboto3)
#         """
#         self._adapter_cls = adapter_cls
#         self._client_factory = client_factory
#
#     async def __aenter__(self):
#         self.client = await self._client_factory().__aenter__()
#         self.adapter: S3Adapter = self._adapter_cls(self.client)
#         self.unit_images = UnitImagesRepository(self.adapter)
#         return self
#
#     async def __aexit__(self, *args):
#         await self.adapter.rollback()
#         await self.adapter.close()
#         await self.client.__aexit__(*args)
#
#     async def commit(self):
#         await self.adapter.commit()
#
#     async def rollback(self):
#         await self.adapter.rollback()
