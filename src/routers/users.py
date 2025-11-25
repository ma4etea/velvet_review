from fastapi import APIRouter, Response

from src.exceptions.not_found import (
    UserNotFoundException,
    UserSessionNotFoundException,
    DeviceIDNotFoundException,
)
from src.routers.dependencies import DepDB, DepRefresh, DepAccess, DepDeviceID, DepCache
from src.routers.http_exceptions.not_found import (
    UserSessionNotFoundHTTPException,
    UserNotFoundHTTPException,
    DeviceIDNotFoundHTTPException,
)
from src.schemas.base import StandardResponse, NullDataResponse
from src.schemas.users import UserResponse
from src.schemas.auths import TokensDTO
from src.services.users import UsersService
from src.utils.files import get_md
from src.utils.swagger_exceptions import exceptions_to_openapi

users_router = APIRouter(prefix="/users", tags=["Пользователи"])


@users_router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    description=get_md("docs/get_me_description.md"),
    responses=exceptions_to_openapi(UserNotFoundHTTPException),
)
async def get_me(db: DepDB, cache: DepCache, payload_access: DepAccess):
    try:
        user = await UsersService(db=db, cache=cache).get_me(user_id=payload_access.user_id)
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    return StandardResponse(data=UserResponse(user=user))


@users_router.post(
    "/logout",
    response_model=NullDataResponse,
    description=get_md("docs/logout_description.md"),
    responses=exceptions_to_openapi(UserSessionNotFoundHTTPException),
)
async def logout(
    db: DepDB,
    response: Response,
    payload_access: DepAccess,
    payload_refresh: DepRefresh,
    device_id: DepDeviceID,
) -> NullDataResponse:
    try:
        await UsersService(db=db).logout_user(
            user_id=payload_access.user_id,
            session_id=payload_refresh.session_id,
            device_id=device_id,
        )
    except DeviceIDNotFoundException:
        raise DeviceIDNotFoundHTTPException
    except UserSessionNotFoundException:
        raise UserSessionNotFoundHTTPException

    for key in TokensDTO.model_fields.keys():
        response.delete_cookie(key)

    return NullDataResponse(message="Вы успешно вышли из системы")
