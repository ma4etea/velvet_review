import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID
from typing import Annotated, Any

import aiofiles
from fastapi import Depends, Request, UploadFile, File, Query

from src.adapters.redis_adapter import redis_client, RedisAdapter
from src.config import settings
from src.database import new_async_session
from src.exceptions.base import (
    InvalidSignatureException,
    ExpiredSignatureException,
    NotAnAccessTokenException,
    NotARefreshTokenException,
)
from src.models.users import RoleUserInStoreEnum, RoleUserInCompanyEnum
from src.routers.http_exceptions.base import (
    InvalidTokenHTTPException,
    ExpiredTokenHTTPException,
    NotAnAccessTokenHTTPException,
    NotARefreshTokenHTTPException,
    UnsupportedImageExtensionHTTPException,
)
from src.routers.http_exceptions.forbidden import AccessForbiddenHTTPException
from src.schemas.base import BaseSchema
from src.schemas.types import IDInt
from src.schemas.query import GetUnitQuery
from src.services.helpers.access_roles import roles_is_administrations
from src.utils.cache.manager import CacheManager
from src.utils.db_manager import DBAsyncManager
from src.utils.s3_manager import get_s3_manager_fabric, S3Manager
from src.utils.tokens_manager import token_manager


async def get_db_manager():
    async with DBAsyncManager(new_async_session) as db:
        yield db


DepDB = Annotated[DBAsyncManager, Depends(get_db_manager)]


async def get_cache_manager():
    async with CacheManager(RedisAdapter(redis_client)) as cache:
        yield cache


DepCache = Annotated[CacheManager, Depends(get_cache_manager)]


async def get_s3_manager():
    async with get_s3_manager_fabric() as s3:
        yield s3


DepS3 = Annotated[S3Manager, Depends(get_s3_manager)]


def get_access_token(request: Request) -> str:
    cookies = request.cookies
    access_token = cookies.get("access_token")
    if not access_token:
        raise InvalidTokenHTTPException
    return access_token


class PayloadAccessToken(BaseSchema):
    user_id: IDInt
    company_role: RoleUserInCompanyEnum
    stores_roles: dict[int, RoleUserInStoreEnum]


def verify_access_token(access_token: str = Depends(get_access_token)) -> dict[str, Any]:
    try:
        payload = token_manager.decode_access_token(access_token)
    except ExpiredSignatureException:
        raise ExpiredTokenHTTPException
    except NotAnAccessTokenException:
        raise NotAnAccessTokenHTTPException
    except InvalidSignatureException:
        raise InvalidTokenHTTPException
    return payload


def get_payload_access_token(
    payload: dict[str, Any] = Depends(verify_access_token),
) -> PayloadAccessToken:
    return PayloadAccessToken.model_validate(payload)


DepAccess = Annotated[PayloadAccessToken, Depends(get_payload_access_token)]


def get_refresh_token(request: Request) -> str:
    cookies = request.cookies
    refresh_token = cookies.get("refresh_token")
    if not refresh_token:
        raise InvalidTokenHTTPException
    return refresh_token


class PayloadRefreshToken(BaseSchema):
    session_id: int


def get_payload_refresh_token(
    refresh_token: str = Depends(get_refresh_token),
) -> PayloadRefreshToken:
    try:
        payload = token_manager.decode_refresh_token(refresh_token)
    except ExpiredSignatureException:
        raise ExpiredTokenHTTPException
    except NotARefreshTokenException:
        raise NotARefreshTokenHTTPException
    except InvalidSignatureException:
        raise InvalidTokenHTTPException
    return PayloadRefreshToken.model_validate(payload)


DepRefresh = Annotated[PayloadRefreshToken, Depends(get_payload_refresh_token)]


def get_device_id(request: Request) -> str | None:
    cookies = request.cookies
    device_id = cookies.get("device_id")
    if not device_id:
        return None
    return str(UUID(device_id))


DepDeviceID = Annotated[str | None, Depends(get_device_id)]


@dataclass
class UploadImagesResult:
    path_to_folder_with_images: str
    total_images: int


async def upload_images_to_tmp(
    files: list[UploadFile] = File(
        ..., description=f"Поддерживаемые форматы: {settings.ALLOWED_EXTENSIONS}"
    ),
) -> UploadImagesResult:
    # todo на уровне Nginx нужно ограничить размер запроса 100мб с расчетом 10 мб на фото если 10 штук
    # todo на уровне middleware нужно ограничить количество файлов до 10
    for file in files:
        if not file.filename:
            raise UnsupportedImageExtensionHTTPException
        if Path(file.filename).suffix.lower() not in settings.ALLOWED_EXTENSIONS:
            raise UnsupportedImageExtensionHTTPException

    upload_tmp_dir = Path(tempfile.mkdtemp(dir="tmp"))

    number = 0
    for number, file in enumerate(files, start=1):
        if not file.filename:
            raise UnsupportedImageExtensionHTTPException
        filename = f"{Path(str(number))}{Path(file.filename).suffix.lower()}"
        file_path = upload_tmp_dir / filename
        async with aiofiles.open(file_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):  # читаем по 1 МБ
                await out_file.write(chunk)

    return UploadImagesResult(str(upload_tmp_dir), number)


DepUploadImages = Annotated[UploadImagesResult, Depends(upload_images_to_tmp)]


def get_unit_query(query: GetUnitQuery = Query()):
    return query


DepGetUnitQuery = Annotated[GetUnitQuery, Depends(get_unit_query)]


def check_admin_access(payload: PayloadAccessToken = Depends(get_payload_access_token)):
    if payload.company_role not in roles_is_administrations:
        raise AccessForbiddenHTTPException
