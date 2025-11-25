from typing import Annotated

from fastapi import APIRouter, Path, Body, Depends

from src.exceptions.base import RoleUserInStoreAlreadyExistsException
from src.exceptions.forbidden import (
    ApproveRegistrationForbiddenException,
    SelfUpdateRoleInCompanyForbiddenException,
    UpdateRoleInCompanyForbiddenException,
    AdminRoleModificationInStoreForbiddenException,
)
from src.exceptions.not_found import (
    UnconfirmedRegistrationNotFoundException,
    UserNotFoundException,
    StoreNotFoundException,
    RoleUserInStoreNotFoundException,
)
from src.models.users import RoleUserInStoreEnum
from src.routers.dependencies import DepCache, DepAccess, DepDB, check_admin_access
from src.routers.http_exceptions.conflict import RoleUserInStoreAlreadyExistsHTTPException
from src.routers.http_exceptions.forbidden import (
    ApproveRegistrationForbiddenHTTPException,
    SelfUpdateRoleInCompanyForbiddenHTTPException,
    UpdateRoleInCompanyForbiddenHTTPException,
    AdminRoleModificationInStoreForbiddenHTTPException,
)
from src.routers.http_exceptions.not_found import (
    UnconfirmedRegistrationNotFoundHTTPException,
    UserNotFoundHTTPException,
    StoreNotFoundHTTPException,
    RoleUserInStoreNotFoundHTTPException,
)
from src.routers.openapi_exemples import (
    openapi_update_role_in_company_examples,
    openapi_assign_user_to_store_examples,
    openapi_update_role_user_in_store_examples,
)
from src.schemas.base import StandardResponse, NullDataResponse
from src.schemas.admins import (
    ApproveRegistrationDTO,
    UpdateCompanyRoleDTO,
    CompanyRoleResponse,
    StoreWithUsersResponse,
    AssignUserToStoreDTO,
    UpdateUserRoleInStore,
)
from src.schemas.types import IDInt
from src.services.admins import AdminsService
from src.services.helpers.access_roles import (
    roles_is_administrations,
    roles_can_update_role_in_company,
    updatable_roles_in_company,
)
from src.services.stores import StoresService
from src.utils.files import get_md
from src.utils.swagger_exceptions import exceptions_to_openapi

admins_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(check_admin_access)],
    tags=["Администратор"],
)


@admins_router.post(
    "/approve",
    description=get_md(
        path_to_md_file="docs/approve_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
    ),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        ApproveRegistrationForbiddenHTTPException, UnconfirmedRegistrationNotFoundHTTPException
    ),
)
async def approve_registration_user(
    db: DepDB, cache: DepCache, payload: DepAccess, dto: ApproveRegistrationDTO
) -> NullDataResponse:
    try:
        message = await AdminsService(db=db, cache=cache).approve_register_user(
            dto=dto, user_role_in_company=payload.company_role
        )
    except ApproveRegistrationForbiddenException:
        raise ApproveRegistrationForbiddenHTTPException
    except UnconfirmedRegistrationNotFoundException:
        raise UnconfirmedRegistrationNotFoundHTTPException

    return NullDataResponse(message=message)


@admins_router.put(
    "/users/{user_id}/company_role",
    description=get_md(
        path_to_md_file="docs/update_role_in_company_description.md",
        can_update_company_role=", ".join(role.value for role in roles_can_update_role_in_company),
        company_roles=", ".join(role.value for role in updatable_roles_in_company),
    ),
    response_model=StandardResponse[CompanyRoleResponse],
    responses=exceptions_to_openapi(
        SelfUpdateRoleInCompanyForbiddenHTTPException,
        UpdateRoleInCompanyForbiddenHTTPException,
        UserNotFoundHTTPException,
    ),
)
async def update_role_in_company(
    db: DepDB,
    cache: DepCache,
    payload: DepAccess,
    user_id: Annotated[IDInt, Path()],
    dto: UpdateCompanyRoleDTO = Body(openapi_examples=openapi_update_role_in_company_examples),
) -> StandardResponse[CompanyRoleResponse]:
    try:
        user = await AdminsService(db=db, cache=cache).update_role_in_company(
            dto=dto,
            self_id=payload.user_id,
            user_id=user_id,
            user_role_in_company=payload.company_role,
        )
    except SelfUpdateRoleInCompanyForbiddenException:
        raise SelfUpdateRoleInCompanyForbiddenHTTPException
    except UpdateRoleInCompanyForbiddenException:
        raise UpdateRoleInCompanyForbiddenHTTPException
    except UserNotFoundException:
        raise UserNotFoundHTTPException

    return StandardResponse(data=CompanyRoleResponse(user=user))


@admins_router.post(
    "/stores/{store_id}/users",
    description=get_md(
        path_to_md_file="docs/assign_user_to_store_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        all_store_roles=", ".join(role.value for role in RoleUserInStoreEnum),
    ),
    response_model=StandardResponse[StoreWithUsersResponse],
    responses=exceptions_to_openapi(
        UserNotFoundHTTPException,
        AdminRoleModificationInStoreForbiddenHTTPException,
        StoreNotFoundHTTPException,
        RoleUserInStoreAlreadyExistsHTTPException,
    ),
)
async def assign_user_to_store(
    db: DepDB,
    cache: DepCache,
    store_id: Annotated[IDInt, Path()],
    dto: AssignUserToStoreDTO = Body(openapi_examples=openapi_assign_user_to_store_examples),
) -> StandardResponse[StoreWithUsersResponse]:
    try:
        store_with_users = await StoresService(db=db, cache=cache).assign_user_to_store(
            dto=dto, store_id=store_id
        )
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except AdminRoleModificationInStoreForbiddenException:
        raise AdminRoleModificationInStoreForbiddenHTTPException
    except StoreNotFoundException:
        raise StoreNotFoundHTTPException
    except RoleUserInStoreAlreadyExistsException:
        raise RoleUserInStoreAlreadyExistsHTTPException

    return StandardResponse(data=StoreWithUsersResponse(store=store_with_users))


@admins_router.put(
    "/stores/{store_id}/users/{user_id}",
    description=get_md(
        path_to_md_file="docs/update_role_user_in_store_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        all_store_roles=", ".join(role.value for role in RoleUserInStoreEnum),
    ),
    response_model=StandardResponse[StoreWithUsersResponse],
    responses=exceptions_to_openapi(
        UserNotFoundHTTPException,
        AdminRoleModificationInStoreForbiddenHTTPException,
        StoreNotFoundHTTPException,
        RoleUserInStoreNotFoundHTTPException,
    ),
)
async def update_role_user_in_store(
    db: DepDB,
    cache: DepCache,
    store_id: Annotated[IDInt, Path()],
    user_id: Annotated[IDInt, Path()],
    dto: UpdateUserRoleInStore = Body(openapi_examples=openapi_update_role_user_in_store_examples),
) -> StandardResponse[StoreWithUsersResponse]:
    try:
        store_with_users = await StoresService(db=db, cache=cache).update_role_user_in_store(
            store_id=store_id, user_id=user_id, dto=dto
        )
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except AdminRoleModificationInStoreForbiddenException:
        raise AdminRoleModificationInStoreForbiddenHTTPException
    except StoreNotFoundException:
        raise StoreNotFoundHTTPException
    except RoleUserInStoreNotFoundException:
        raise RoleUserInStoreNotFoundHTTPException

    return StandardResponse(data=StoreWithUsersResponse(store=store_with_users))


@admins_router.delete(
    "/stores/{store_id}/users/{user_id}",
    description=get_md(
        path_to_md_file="docs/unassign_user_from_store_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
    ),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        UserNotFoundHTTPException,
        AdminRoleModificationInStoreForbiddenHTTPException,
        StoreNotFoundHTTPException,
        RoleUserInStoreNotFoundHTTPException,
    ),
)
async def unassign_user_from_store(
    db: DepDB,
    cache: DepCache,
    store_id: Annotated[IDInt, Path()],
    user_id: Annotated[IDInt, Path()],
) -> NullDataResponse:
    try:
        await StoresService(db=db, cache=cache).unassign_user_from_store(
            store_id=store_id, user_id=user_id
        )
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except AdminRoleModificationInStoreForbiddenException:
        raise AdminRoleModificationInStoreForbiddenHTTPException
    except StoreNotFoundException:
        raise StoreNotFoundHTTPException
    except RoleUserInStoreNotFoundException:
        raise RoleUserInStoreNotFoundHTTPException

    return NullDataResponse(message="Роль пользователя успешно удалена из магазина")


@admins_router.get(
    "/stores/{store_id}/users",
    description=get_md(
        path_to_md_file="docs/get_store_with_users_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
    ),
    response_model=StandardResponse[StoreWithUsersResponse],
    responses=exceptions_to_openapi(
        StoreNotFoundHTTPException,
    ),
)
async def get_store_with_users(
    db: DepDB,
    store_id: Annotated[IDInt, Path()],
) -> StandardResponse[StoreWithUsersResponse]:
    try:
        store_with_users = await StoresService(db=db).get_store_with_users(store_id=store_id)
    except StoreNotFoundException:
        raise StoreNotFoundHTTPException

    return StandardResponse(data=StoreWithUsersResponse(store=store_with_users))
