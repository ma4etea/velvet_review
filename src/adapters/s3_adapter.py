import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable

from botocore.exceptions import ClientError

from src.adapters.custom_s3_client import CustomAioBaseClient, CustomAIOBoto3Session
from mypy_boto3_s3.type_defs import (
    ObjectIdentifierTypeDef,
    CopySourceTypeDef,
)

from src.config import settings
from src.logging_config import logger


@asynccontextmanager
async def get_s3_client() -> AsyncGenerator[CustomAioBaseClient, None]:
    session = CustomAIOBoto3Session()
    async with session.client(
        service_name="s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        verify=False,
    ) as s3:
        yield s3


class S3Adapter:
    def __init__(self, s3_client: CustomAioBaseClient):
        self.client = s3_client
        self.pending_keys: defaultdict[str, list[ObjectIdentifierTypeDef]] = defaultdict(list)
        self.deleting_keys: defaultdict[str, list[ObjectIdentifierTypeDef]] = defaultdict(list)

    async def delete(self, bucket: str, keys: tuple[str, ...]):
        """
        Удаление через rename нужно для того, чтобы rollback мог все вернуть(консистентность данных)
        """
        if not keys:
            raise ValueError("Должен быть указан хотя бы один ключ")
        renames: list[Awaitable[None]] = []
        for key in keys:
            deleting_key = f"deleting/{key}"
            self.deleting_keys[bucket].append({"Key": deleting_key})
            renames.append(self.rename(bucket=bucket, src_key=key, dst_key=deleting_key))
        await asyncio.gather(*renames)

    async def commit(self):
        if self.pending_keys:
            await asyncio.gather(
                *[
                    self.rename(
                        bucket=bucket,
                        src_key=key["Key"],
                        dst_key=key["Key"].removeprefix("pending/"),
                    )
                    for bucket, keys in self.pending_keys.items()
                    for key in keys
                ]
            )
            self.pending_keys.clear()

        if self.deleting_keys:
            await asyncio.gather(
                *[
                    self.client.delete_object(Bucket=bucket, Key=key["Key"])
                    for bucket, keys in self.deleting_keys.items()
                    for key in keys
                ]
            )
            self.deleting_keys.clear()

    async def rollback(self):
        if self.deleting_keys:
            await asyncio.gather(
                *[
                    self.rename(
                        bucket=bucket,
                        src_key=key["Key"],
                        dst_key=key["Key"].removeprefix("deleting/"),
                    )
                    for bucket, keys in self.deleting_keys.items()
                    for key in keys
                ]
            )
            self.deleting_keys.clear()

        if self.pending_keys:
            await asyncio.gather(
                *[
                    self.client.delete_object(Bucket=bucket, Key=key["Key"])
                    for bucket, keys in self.pending_keys.items()
                    for key in keys
                ]
            )
            self.pending_keys.clear()

    async def upload_file(self, file_path: str, bucket: str, key: str) -> None:
        """
        Загружает файл в указанный S3/MinIO bucket.

        Args:
            bucket: В какой bucket загрузить
            file_path: Путь до файла
            key: Уникальное название файла в bucket

        Raises:
            FileNotFoundError: Если локальный файл не найден
            botocore.exceptions.ClientError: Ошибки при работе с S3/MinIO
            botocore.exceptions.ParamValidationError: Некорректные параметры
            botocore.exceptions.EndpointConnectionError: Ошибка соединения с сервером

        Returns:
            None
        """
        pending_key = f"pending/{key}"
        self.pending_keys[bucket].append({"Key": pending_key})
        await self.client.upload_file(
            Filename=file_path,
            Bucket=bucket,
            Key=pending_key,
        )

    async def rename(self, bucket: str, src_key: str, dst_key: str):
        """Копирует в новый путь и удаляет старый"""
        source: CopySourceTypeDef = {"Bucket": bucket, "Key": src_key}
        await self.client.copy_object(Bucket=bucket, Key=dst_key, CopySource=source)

        await self.client.delete_object(Bucket=bucket, Key=src_key)

    async def check_key(self, bucket: str, key: str) -> bool:
        try:
            await self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as exc:
            error = exc.response.get("Error")
            code = error.get("Code") if error else None
            if code and code == "404":
                logger.debug(f"Не найден:{key=}")
                return False
            raise

    async def close(self):
        await self.client.close()
