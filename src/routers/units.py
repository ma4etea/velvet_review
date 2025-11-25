from typing import Annotated

from fastapi import APIRouter, Path, Query, Body

from src.config import settings
from src.exceptions.base import (
    UnitHaveTransactionsException,
    UnitImagesLimitException,
    UnitImageIsMainException,
)
from src.exceptions.forbidden import (
    UnitModificationInStoreForbiddenException,
    UnitReadInStoreForbiddenException,
    UnitReadInAllStoresForbiddenException,
)
from src.exceptions.not_found import (
    UnitNotFoundException,
    StoreNotFoundException,
    UnitImageNotFoundException,
)
from src.routers.dependencies import (
    DepDB,
    DepAccess,
    DepUploadImages,
    DepS3,
    DepGetUnitQuery,
    DepCache,
)
from src.routers.http_exceptions.base import (
    UnsupportedImageExtensionHTTPException,
)
from src.routers.http_exceptions.conflict import (
    UnitHaveTransactionsHTTPException,
    UnitImagesLimitHTTPException,
    UnitImageIsMainHTTPException,
)
from src.routers.http_exceptions.forbidden import (
    UnitModificationInStoreForbiddenHTTPException,
    AccessForbiddenHTTPException,
    UnitReadInStoreForbiddenHTTPException,
    UnitReadInAllStoresForbiddenHTTPException,
    UnitModificationForbiddenHTTPException,
)
from src.routers.http_exceptions.not_found import (
    UnitNotFoundHTTPException,
    StoreNotFoundHTTPException,
    UnitImageNotFoundHTTPException,
)
from src.routers.openapi_exemples import openapi_add_unit_examples
from src.schemas.base import StandardResponse, NullDataResponse
from src.schemas.types import IDInt, UnitField
from src.schemas.units import (
    UnitWithFieldsResponse,
    AddUnitDTO,
    EditUnitDTO,
    UnitResponse,
    UnitsWithMainImageResponse,
)
from src.schemas.query import UnitsQuery
from src.services.helpers.access_roles import (
    roles_is_administrations,
    roles_can_write_unit_in_store,
    roles_can_read_unit_in_store,
)
from src.services.units import UnitsService
from src.utils.files import get_md
from src.utils.swagger_exceptions import exceptions_to_openapi

units_router = APIRouter(prefix="/units", tags=["Товары"])


@units_router.post(
    "",
    description=get_md(
        "docs/add_unit_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_add_unit=", ".join(role.value for role in roles_can_write_unit_in_store),
    ),
    response_model=StandardResponse[UnitResponse],
    responses=exceptions_to_openapi(StoreNotFoundHTTPException, StoreNotFoundHTTPException),
)
async def add_unit(
    db: DepDB,
    payload: DepAccess,
    data: AddUnitDTO = Body(openapi_examples=openapi_add_unit_examples),
) -> StandardResponse[UnitResponse]:
    try:
        unit = await UnitsService(db).add_unit(
            dto=data,
            user_roles_in_stores=payload.stores_roles,
            user_role_in_company=payload.company_role,
        )
    except StoreNotFoundException:
        raise StoreNotFoundHTTPException
    except UnitModificationInStoreForbiddenException:
        raise UnitModificationInStoreForbiddenHTTPException
    return StandardResponse(data=UnitResponse(unit=unit))


@units_router.get(
    "",
    description=get_md(
        path_to_md_file="docs/get_units_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_get_units=", ".join(role.value for role in roles_can_read_unit_in_store),
    ),
    response_model=StandardResponse[UnitsWithMainImageResponse],
    responses=exceptions_to_openapi(
        UnitNotFoundHTTPException,
        StoreNotFoundHTTPException,
        UnitReadInStoreForbiddenHTTPException,
        UnitReadInAllStoresForbiddenHTTPException,
    ),
)
async def get_units(
    db: DepDB,
    cache: DepCache,
    payload: DepAccess,
    pag: Annotated[UnitsQuery, Query()],
) -> StandardResponse[UnitsWithMainImageResponse]:
    try:
        units = await UnitsService(db=db, cache=cache).get_units(
            offset=pag.offset,
            limit=pag.limit,
            search_term=pag.search_term,
            store_id=pag.store_id,
            user_role_in_company=payload.company_role,
            user_roles_in_stores=payload.stores_roles,
            sort_order=pag.sort_order,
            sort_by=pag.sort_by,
        )
    except UnitNotFoundException:
        raise UnitNotFoundHTTPException
    except StoreNotFoundException:
        raise StoreNotFoundHTTPException
    except UnitReadInStoreForbiddenException:
        raise UnitReadInStoreForbiddenHTTPException
    except UnitReadInAllStoresForbiddenException:
        raise UnitReadInAllStoresForbiddenHTTPException
    return StandardResponse(data=UnitsWithMainImageResponse(units=units))


@units_router.get(
    "/{unit_id}",
    description=get_md(
        path_to_md_file="docs/get_unit_description.md",
        fields=", ".join(field.value for field in UnitField),
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_get_unit=", ".join(role.value for role in roles_can_read_unit_in_store),
    ),
    response_model=StandardResponse[UnitWithFieldsResponse],
    responses=exceptions_to_openapi(UnitNotFoundHTTPException, AccessForbiddenHTTPException),
)
async def get_unit(
    db: DepDB, payload: DepAccess, unit_id: Annotated[IDInt, Path()], query: DepGetUnitQuery
) -> StandardResponse[UnitWithFieldsResponse]:
    try:
        fields = tuple(query.field) if query.field else None
        unit_with_fields = await UnitsService(db).get_unit(
            unit_id=unit_id,
            user_roles_in_stores=payload.stores_roles,
            user_role_in_company=payload.company_role,
            fields=fields,
        )
    except UnitReadInStoreForbiddenException:
        raise AccessForbiddenHTTPException
    except UnitNotFoundException:
        raise UnitNotFoundHTTPException
    return StandardResponse(data=UnitWithFieldsResponse(unit=unit_with_fields))


@units_router.patch(
    "/{unit_id}",
    description=get_md(
        "docs/edit_unit_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_edit_unit=", ".join(role.value for role in roles_can_write_unit_in_store),
    ),
    response_model=StandardResponse[UnitResponse],
    responses=exceptions_to_openapi(
        UnitNotFoundHTTPException,
        UnitModificationForbiddenHTTPException,
        UnitImageNotFoundHTTPException,
    ),
)
async def edit_unit(
    db: DepDB, payload: DepAccess, dto: EditUnitDTO, unit_id: Annotated[IDInt, Path()]
) -> StandardResponse[UnitResponse]:
    try:
        unit = await UnitsService(db).edit_unit(
            dto=dto,
            unit_id=unit_id,
            user_roles_in_stores=payload.stores_roles,
            user_role_in_company=payload.company_role,
        )
    except UnitReadInStoreForbiddenException:
        raise UnitModificationForbiddenHTTPException
    except UnitNotFoundException:
        raise UnitNotFoundHTTPException
    except UnitImageNotFoundException:
        raise UnitImageNotFoundHTTPException
    return StandardResponse(data=UnitResponse(unit=unit))


@units_router.delete(
    "/{unit_id}",
    description=get_md(
        path_to_md_file="docs/remove_unit_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_delete_unit=", ".join(role.value for role in roles_can_write_unit_in_store),
    ),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        AccessForbiddenHTTPException, UnitNotFoundHTTPException, UnitHaveTransactionsHTTPException
    ),
)
async def delete_unit(
    db: DepDB, s3: DepS3, payload: DepAccess, unit_id: Annotated[IDInt, Path()]
) -> NullDataResponse:
    try:
        await UnitsService(db=db, s3=s3).delete_unit(
            unit_id=unit_id,
            user_roles_in_stores=payload.stores_roles,
            user_role_in_company=payload.company_role,
        )
    except UnitModificationInStoreForbiddenException:
        raise AccessForbiddenHTTPException
    except UnitNotFoundException:
        raise UnitNotFoundHTTPException
    except UnitHaveTransactionsException:
        raise UnitHaveTransactionsHTTPException
    return NullDataResponse(message="Товар удалён")


@units_router.post(
    "/{unit_id}/images",
    description=get_md(
        "docs/upload_images_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_upload_images=", ".join(role.value for role in roles_can_write_unit_in_store),
        supported_extensions=", ".join(ext for ext in settings.ALLOWED_EXTENSIONS),
        max_images=str(settings.UNIT_IMAGES_LIMIT),
    ),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        UnitNotFoundHTTPException,
        UnitModificationInStoreForbiddenHTTPException,
        UnsupportedImageExtensionHTTPException,
        UnitImagesLimitHTTPException,
    ),
)
async def upload_images(
    db: DepDB, payload: DepAccess, result: DepUploadImages, unit_id: Annotated[IDInt, Path()]
) -> NullDataResponse:
    try:
        await UnitsService(db=db).create_task_upload_images(
            path_to_folder_with_images=result.path_to_folder_with_images,
            total_images=result.total_images,
            unit_id=unit_id,
            user_roles_in_stores=payload.stores_roles,
            user_role_in_company=payload.company_role,
        )
    except UnitNotFoundException:
        raise UnitNotFoundHTTPException
    except UnitModificationInStoreForbiddenException:
        raise UnitModificationInStoreForbiddenHTTPException
    except UnitImagesLimitException:
        raise UnitImagesLimitHTTPException

    return NullDataResponse(message="Изображения для товара получены и находятся в обработке")


@units_router.delete(
    "/{unit_id}/images/{image_id}",
    description=get_md(
        path_to_md_file="docs/delete_image_description.md",
        admin_roles=", ".join(role.value for role in roles_is_administrations),
        can_delete_image=", ".join(role.value for role in roles_can_write_unit_in_store),
    ),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        UnitNotFoundHTTPException,
        UnitModificationInStoreForbiddenHTTPException,
        UnitImageNotFoundHTTPException,
        UnitImageIsMainHTTPException,
    ),
)
async def delete_unit_image(
    db: DepDB,
    s3: DepS3,
    payload: DepAccess,
    unit_id: Annotated[IDInt, Path()],
    image_id: Annotated[IDInt, Path()],
) -> NullDataResponse:
    try:
        await UnitsService(db=db, s3=s3).delete_unit_image(
            unit_id=unit_id,
            image_id=image_id,
            user_roles_in_stores=payload.stores_roles,
            user_role_in_company=payload.company_role,
        )
    except UnitNotFoundException:
        raise UnitNotFoundHTTPException
    except UnitModificationInStoreForbiddenException:
        raise UnitModificationInStoreForbiddenHTTPException
    except UnitImageNotFoundException:
        raise UnitImageNotFoundHTTPException
    except UnitImageIsMainException:
        raise UnitImageIsMainHTTPException
    return NullDataResponse(message="Файл удален")
