from typing import Annotated

from fastapi import APIRouter, Path, Query, Body

from src.exceptions.base import UnitOutOfStockException
from src.exceptions.conflict import UnitBelongAnotherStoreException
from src.exceptions.forbidden import (
    ActionAccessForbiddenException,
    StoreAccessForbiddenException,
    AllStoresAccessForbiddenException,
)
from src.exceptions.not_found import (
    ActionNotFoundException,
    StoreNotFoundException,
    UnitNotFoundException,
)
from src.models.actions import ActionEnum
from src.routers.dependencies import DepDB, DepAccess, DepCache
from src.routers.http_exceptions.bad_request import UnitBelongAnotherStoreHTTPException
from src.routers.http_exceptions.conflict import UnitOutOfStockHTTPException
from src.routers.http_exceptions.forbidden import (
    ActionAccessForbiddenHTTPException,
    StoreAccessForbiddenHTTPException,
    AllStoresAccessForbiddenHTTPException,
)
from src.routers.http_exceptions.not_found import (
    ActionNotFoundHTTPException,
    StoreNotFoundHTTPException,
    UnitNotFoundHTTPException,
)
from src.routers.openapi_exemples import openapi_add_action_examples
from src.schemas.actions import (
    ActionsWithUnitsResponse,
    ActionWithUnitsResponse,
    ActionsQuery,
    AddActionDTO,
    ActionResponse,
    ActionWithUnitsTransactionsDTO,
)
from src.schemas.base import StandardResponse, PaginationItems
from src.schemas.types import IDInt
from src.services.actions import ActionsService
from src.services.helpers.access_roles import (
    roles_is_administrations,
    roles_can_add_stock,
    roles_can_sales,
    roles_can_sales_return,
    roles_can_write_off,
    roles_can_new_price,
    roles_can_stock_return,
    roles_can_read_action_in_store,
)
from src.utils.files import get_md
from src.utils.swagger_exceptions import exceptions_to_openapi

actions_router = APIRouter(prefix="/actions", tags=["Действия с товаром"])


@actions_router.post(
    "",
    description=get_md(
        path_to_md_file="docs/add_action_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        action_1=ActionEnum.addStock.value,
        roles_can_1=", ".join(role.value for role in roles_can_add_stock),
        action_2=ActionEnum.sales.value,
        roles_can_2=", ".join(role.value for role in roles_can_sales),
        action_3=ActionEnum.salesReturn.value,
        roles_can_3=", ".join(role.value for role in roles_can_sales_return),
        action_4=ActionEnum.writeOff.value,
        roles_can_4=", ".join(role.value for role in roles_can_write_off),
        action_5=ActionEnum.newPrice.value,
        roles_can_5=", ".join(role.value for role in roles_can_new_price),
        action_6=ActionEnum.stockReturn.value,
        roles_can_6=", ".join(role.value for role in roles_can_stock_return),
    ),
    response_model=StandardResponse[ActionResponse],
    responses=exceptions_to_openapi(
        StoreNotFoundHTTPException,
        ActionAccessForbiddenHTTPException,
        UnitNotFoundHTTPException,
        UnitBelongAnotherStoreHTTPException,
        UnitOutOfStockHTTPException,
    ),
)
async def add_action(
    db: DepDB,
    payload: DepAccess,
    body: AddActionDTO = Body(openapi_examples=openapi_add_action_examples),
) -> StandardResponse[ActionResponse]:
    try:
        action = await ActionsService(db).add_action(
            user_id=payload.user_id,
            dto=body,
            user_roles_in_stores=payload.stores_roles,
            user_role_in_company=payload.company_role,
        )
    except StoreNotFoundException:
        raise StoreNotFoundHTTPException
    except ActionAccessForbiddenException:
        raise ActionAccessForbiddenHTTPException
    except UnitNotFoundException:
        raise UnitNotFoundHTTPException
    except UnitBelongAnotherStoreException:
        raise UnitBelongAnotherStoreHTTPException
    except UnitOutOfStockException:
        raise UnitOutOfStockHTTPException
    return StandardResponse(
        data=ActionResponse(action=action), message="Успех: транзакция исполнена"
    )


@actions_router.get(
    "",
    description=get_md(
        path_to_md_file="docs/get_actions_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_get_actions=", ".join(role.value for role in roles_can_read_action_in_store),
    ),
    response_model=StandardResponse[ActionsWithUnitsResponse],
    responses=exceptions_to_openapi(
        StoreNotFoundHTTPException,
        AllStoresAccessForbiddenHTTPException,
        StoreAccessForbiddenHTTPException,
        ActionNotFoundHTTPException,
    ),
)
async def get_actions(
    db: DepDB,
    cache: DepCache,
    payload: DepAccess,
    query: Annotated[ActionsQuery, Query()],
) -> StandardResponse[ActionsWithUnitsResponse]:
    try:
        actions, pagination = await ActionsService(db=db, cache=cache).get_actions(
            offset=query.offset,
            limit=query.limit,
            search_term=query.search_term,
            user_id=payload.user_id,
            store_id=query.store_id,
            user_role_in_company=payload.company_role,
            user_roles_in_stores=payload.stores_roles,
        )
    except StoreNotFoundException:
        raise StoreNotFoundHTTPException
    except AllStoresAccessForbiddenException:
        raise AllStoresAccessForbiddenHTTPException
    except StoreAccessForbiddenException:
        raise StoreAccessForbiddenHTTPException
    except ActionNotFoundException:
        raise ActionNotFoundHTTPException

    return StandardResponse(
        data=ActionsWithUnitsResponse(
            actions=PaginationItems[ActionWithUnitsTransactionsDTO](
                items=actions, pagination=pagination
            )
        )
    )


@actions_router.get(
    "/{action_id}",
    description=get_md(
        path_to_md_file="docs/get_action_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_get_actions=", ".join(role.value for role in roles_can_read_action_in_store),
    ),
    response_model=StandardResponse[ActionWithUnitsResponse],
    responses=exceptions_to_openapi(ActionNotFoundHTTPException, StoreAccessForbiddenHTTPException),
)
async def get_action(
    db: DepDB, cache: DepCache, payload: DepAccess, action_id: Annotated[IDInt, Path()]
) -> StandardResponse[ActionWithUnitsResponse]:
    try:
        action_with_units = await ActionsService(db=db, cache=cache).get_action(
            action_id=action_id,
            user_roles_in_stores=payload.stores_roles,
            user_role_in_company=payload.company_role,
        )
    except ActionNotFoundException:
        raise ActionNotFoundHTTPException
    except StoreAccessForbiddenException:
        raise StoreAccessForbiddenHTTPException
    return StandardResponse(data=ActionWithUnitsResponse(action=action_with_units))
