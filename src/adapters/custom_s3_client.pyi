from __future__ import annotations
from typing import Any, AsyncContextManager

# --- Типы из mypy_boto3_s3 ---
from mypy_boto3_s3.type_defs import (
    CopySourceTypeDef,
    DeleteTypeDef,
    HeadObjectOutputTypeDef,
)

class CustomAioBaseClient:
    """Асинхронный базовый клиент, оборачивающий botocore BaseClient."""

    async def upload_file(
        self,
        Filename: str,
        Bucket: str,
        Key: str,
        ExtraArgs: dict[str, Any] | None = ...,
        Callback: Any | None = ...,
        Config: Any | None = ...,
    ) -> None: ...
    async def copy_object(
        self,
        Bucket: str,
        Key: str,
        CopySource: CopySourceTypeDef,
        ExtraArgs: dict[str, Any] | None = ...,
    ) -> dict[str, Any]: ...
    async def delete_object(
        self,
        Bucket: str,
        Key: str,
    ) -> dict[str, Any]: ...
    async def delete_objects(
        self,
        Bucket: str,
        Delete: DeleteTypeDef,
        MFA: str | None = ...,
        RequestPayer: str | None = ...,
        BypassGovernanceRetention: bool | None = ...,
        ExpectedBucketOwner: str | None = ...,
        ChecksumAlgorithm: str | None = ...,
    ) -> dict[str, Any]: ...
    async def head_object(
        self,
        Bucket: str,
        Key: str,
    ) -> HeadObjectOutputTypeDef: ...
    async def close(self) -> None: ...

class CustomAIOBoto3Session:
    """
    Custom typed subclass of aioboto3.Session.
    This stub improves IDE/type checker support for async S3 client.
    """

    def client(
        self,
        service_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncContextManager[CustomAioBaseClient]: ...
