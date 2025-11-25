from typing import Annotated

from pydantic import Field

from src.models.notifications import NotificationType, NotificationTargetObject
from src.schemas.base import BaseSchema
from src.schemas.mixin import PatchValidatorMixin
from src.schemas.types import TitleStr, IDInt


class AddNotificationDTO(BaseSchema):
    title: TitleStr
    body: str
    type: NotificationType = NotificationType.info
    is_read: bool = False
    user_id: IDInt
    target_object: NotificationTargetObject | None = None
    target_key: Annotated[
        str | None,
        Field(min_length=0, max_length=320, description="Key или id например email или 1"),
    ] = None


class NotificationDTO(BaseSchema):
    id: int
    title: str
    body: str
    type: NotificationType
    is_read: bool
    user_id: int
    target_object: NotificationTargetObject | None
    target_key: str


class NotificationsResponse(BaseSchema):
    notifications: list[NotificationDTO]


class EditNotificationDTO(PatchValidatorMixin, BaseSchema):
    is_read: bool | None = None


class NotificationResponse(BaseSchema):
    notification: NotificationDTO
