from sqlalchemy import select, desc

from src.models.notifications import NotificationORM
from src.repositories.db.base import BaseRepository
from src.repositories.db.mappers.mappers import NotificationsDataMapper
from src.schemas.types import SortOrder, SortNotificationBy
from src.schemas.notifications import NotificationDTO


class NotificationsRepository(BaseRepository[NotificationORM, NotificationDTO]):
    model = NotificationORM
    mapper = NotificationsDataMapper

    async def get_notifications(
        self,
        user_id: int,
        offset: int,
        limit: int,
        sort_order: SortOrder = SortOrder.desc,
        sort_by: SortNotificationBy = SortNotificationBy.id,
    ) -> list[NotificationDTO]:
        """Получить список уведомлений для пользователя"""

        query = (
            select(self.model)
            .select_from(self.model)
            .filter_by(user_id=user_id)
            .offset(offset)
            .limit(limit)
        )

        order_column = getattr(self.model, sort_by)
        query = query.order_by(desc(order_column) if sort_order == SortOrder.desc else order_column)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self.mapper.to_domain(model) for model in models]
