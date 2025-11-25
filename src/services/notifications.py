from src.schemas.types import SortOrder, SortNotificationBy
from src.services.base import BaseService
from src.exceptions.not_found import (
    NotificationNotFoundException,
    ObjectNotFoundException,
    ForeignKeyNotFoundException,
    UserNotFoundException,
)
from src.schemas.notifications import NotificationDTO, EditNotificationDTO


class NotificationsService(BaseService):
    async def get_notifications(
        self,
        user_id: int,
        offset: int,
        limit: int,
        sort_order: SortOrder,
        sort_by: SortNotificationBy,
    ) -> list[NotificationDTO]:
        """
        :raise NotificationNotFoundException: Если не найдено уведомлений для пользователя.
        """
        notifications = await self.db.notifications.get_notifications(
            user_id=user_id, offset=offset, limit=limit, sort_order=sort_order, sort_by=sort_by
        )
        if not notifications:
            raise NotificationNotFoundException
        return notifications

    async def edit_notification(
        self, user_id: int, notification_id: int, dto: EditNotificationDTO
    ) -> NotificationDTO:
        """
        :raise UserNotFoundException: Если пользователь не найден.
        :raise NotificationNotFoundException: Если уведомления не найдено.
        """
        try:
            notification: NotificationDTO = await self.db.notifications.edit(
                dto=dto, exclude_unset=True, id=notification_id, user_id=user_id
            )
            await self.db.commit()
        except ForeignKeyNotFoundException:
            raise UserNotFoundException
        except ObjectNotFoundException:
            raise NotificationNotFoundException
        return notification

    async def delete_notification(self, user_id: int, notification_id: int):
        """
        :raise NotificationNotFoundException: Если уведомления не найдено.
        """
        try:
            await self.db.notifications.delete(id=notification_id, user_id=user_id)
        except ObjectNotFoundException:
            raise NotificationNotFoundException
        await self.db.commit()
