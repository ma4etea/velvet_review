from typing import Annotated

from fastapi import Query, APIRouter, Path

from src.exceptions.not_found import NotificationNotFoundException, UserNotFoundException
from src.routers.dependencies import DepDB, DepAccess
from src.routers.http_exceptions.not_found import (
    NotificationNotFoundHTTPException,
    UserNotFoundHTTPException,
)
from src.schemas.base import StandardResponse, NullDataResponse
from src.schemas.query import NotificationsQuery
from src.schemas.types import IDInt
from src.schemas.notifications import (
    NotificationsResponse,
    EditNotificationDTO,
    NotificationResponse,
)
from src.services.notifications import NotificationsService
from src.utils.files import get_md
from src.utils.swagger_exceptions import exceptions_to_openapi

notifications_router = APIRouter(prefix="/notifications", tags=["Уведомления для пользователя"])


@notifications_router.get(
    "",
    response_model=StandardResponse[NotificationsResponse],
    description=get_md("docs/msg_description.md"),
    responses=exceptions_to_openapi(NotificationNotFoundHTTPException),
)
async def get_notifications(
    db: DepDB,
    payload: DepAccess,
    pag: Annotated[NotificationsQuery, Query()],
) -> StandardResponse[NotificationsResponse]:
    try:
        user_messages = await NotificationsService(db=db).get_notifications(
            offset=pag.offset,
            limit=pag.limit,
            user_id=payload.user_id,
            sort_order=pag.sort_order,
            sort_by=pag.sort_by,
        )
    except NotificationNotFoundException:
        raise NotificationNotFoundHTTPException

    return StandardResponse(data=NotificationsResponse(notifications=user_messages))


@notifications_router.patch(
    "/{notification_id}",
    description=get_md("docs/edit_notification_description.md"),
    response_model=StandardResponse[NotificationResponse],
    responses=exceptions_to_openapi(UserNotFoundHTTPException, NotificationNotFoundHTTPException),
)
async def edit_notification(
    db: DepDB,
    payload: DepAccess,
    dto: EditNotificationDTO,
    notification_id: Annotated[IDInt, Path()],
) -> StandardResponse[NotificationResponse]:
    try:
        notification = await NotificationsService(db=db).edit_notification(
            user_id=payload.user_id, notification_id=notification_id, dto=dto
        )
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except NotificationNotFoundException:
        raise NotificationNotFoundHTTPException

    return StandardResponse(data=NotificationResponse(notification=notification))


@notifications_router.delete(
    "/{notification_id}",
    description=get_md("docs/delete_notification_description.md"),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(NotificationNotFoundHTTPException),
)
async def delete_notification(
    db: DepDB, payload: DepAccess, notification_id: Annotated[IDInt, Path()]
) -> NullDataResponse:
    try:
        await NotificationsService(db=db).delete_notification(
            user_id=payload.user_id, notification_id=notification_id
        )
    except NotificationNotFoundException:
        raise NotificationNotFoundHTTPException
    return NullDataResponse(message="Уведомление удалено.")
