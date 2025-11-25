from fastapi import APIRouter, Depends

from src.routers.actions import actions_router
from src.routers.dependencies import verify_access_token
from src.routers.files import files_router
from src.routers.http_exceptions.base import (
    ExpiredTokenHTTPException,
    NotAnAccessTokenHTTPException,
    InvalidTokenHTTPException,
)
from src.routers.notifications import notifications_router
from src.routers.stores import stores_router
from src.routers.units import units_router
from src.routers.users import users_router
from src.routers.auths import auth_router
from src.routers.admins import admins_router
from src.utils.swagger_exceptions import exceptions_to_openapi

public_router = APIRouter(
    prefix="/public",
    # dependencies=[Depends(verify_app_secret)],
)

public_router.include_router(auth_router)

protected_router = APIRouter(
    prefix="/protected",
    dependencies=[Depends(verify_access_token)],
    responses=exceptions_to_openapi(
        ExpiredTokenHTTPException, NotAnAccessTokenHTTPException, InvalidTokenHTTPException
    ),
)

protected_router.include_router(admins_router)
protected_router.include_router(notifications_router)
protected_router.include_router(users_router)
protected_router.include_router(stores_router)
protected_router.include_router(units_router)
protected_router.include_router(actions_router)
protected_router.include_router(files_router)
