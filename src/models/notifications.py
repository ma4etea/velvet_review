from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, func, Boolean, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import BaseModel


class NotificationTargetObject(str, Enum):
    users = "users"


class NotificationType(str, Enum):
    approves = "approves"
    info = "info"


class NotificationORM(BaseModel):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    body: Mapped[str] = mapped_column(String(255), default="")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    user_id: Mapped[int] = mapped_column(
        ForeignKey(column="users.id", name="notifications_user_id_fkey", ondelete="CASCADE"),
        index=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        SQLAlchemyEnum(NotificationType, name="notification_type_enum"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    target_object: Mapped[NotificationTargetObject] = mapped_column(
        SQLAlchemyEnum(NotificationTargetObject, name="notification_target_object_enum"),
        nullable=True,
    )
    target_key: Mapped[str] = mapped_column(String(320), nullable=True)
