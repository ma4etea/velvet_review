from fastapi import APIRouter

from src.exceptions.conflict import StoreAlreadyExistsException
from src.exceptions.forbidden import CreateStoreForbiddenException
from src.routers.dependencies import DepDB, DepAccess
from src.routers.http_exceptions.conflict import StoreAlreadyExistsHTTPException
from src.routers.http_exceptions.forbidden import CreateStoreForbiddenHTTPException
from src.schemas.base import StandardResponse
from src.schemas.stores import AddStoreDTO, StoreResponse
from src.services.helpers.access_roles import roles_is_administrations
from src.services.stores import StoresService
from src.utils.files import get_md
from src.utils.swagger_exceptions import exceptions_to_openapi

stores_router = APIRouter(prefix="/stores", tags=["Торговые точки"])


@stores_router.post(
    "",
    description=get_md(
        "docs/create_store_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
    ),
    response_model=StandardResponse[StoreResponse],
    responses=exceptions_to_openapi(
        CreateStoreForbiddenHTTPException,
        StoreAlreadyExistsHTTPException,
    ),
)
async def create_store(
    db: DepDB, payload: DepAccess, data: AddStoreDTO
) -> StandardResponse[StoreResponse]:
    try:
        store = await StoresService(db).create_store(
            dto=data, user_role_in_company=payload.company_role
        )
    except CreateStoreForbiddenException:
        raise CreateStoreForbiddenHTTPException
    except StoreAlreadyExistsException:
        raise StoreAlreadyExistsHTTPException
    return StandardResponse(data=StoreResponse(store=store))
