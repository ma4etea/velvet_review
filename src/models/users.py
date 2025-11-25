import typing
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum, UniqueConstraint
from sqlalchemy import DateTime, func, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

from src.utils.time_manager import get_expiration_refresh_token

if typing.TYPE_CHECKING:
    from src.models.units import StoreORM
    from src.models.notifications import NotificationORM


class RoleUserInStoreEnum(str, Enum):
    """# todo список ролей для магазина
    | Роль                  | Ключ         | Описание                                                                                                               |
    | --------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------- |
    | **Владелец**          | `owner`      | Создатель магазина, имеет полный контроль — может удалять магазин, назначать администраторов, управлять всеми данными. |
    | **Администратор**     | `admin`      | Управляет товарами, заказами, сотрудниками, но не может удалить магазин или изменить владельца.                        |
    | **Менеджер**          | `manager`    | Может добавлять и редактировать товары, работать с заказами, клиентами, но не управляет пользователями.                |
    | **Кассир / Продавец** | `seller`     | Работает с заказами, проводит продажи, печатает чеки. Не управляет товарами и пользователями.                          |
    | **Сотрудник склада**  | `warehouse`  | Управляет остатками, приёмом и отгрузкой товаров, не имеет доступа к заказам.                                          |
    | **Маркетолог**        | `marketer`   | Работает с рекламой, акциями и аналитикой. Не управляет товарами или пользователями.                                   |
    | **Бухгалтер**         | `accountant` | Доступ к финансовым отчётам, не изменяет заказы или товары.                                                            |
    | **Наблюдатель**       | `viewer`     | Только читает данные, без возможности что-либо менять.                                                                 |
    """

    manager = "manager"
    seller = "seller"
    viewer = "viewer"


class RoleUserInCompanyEnum(str, Enum):
    owner = "owner"
    member = "member"
    admin = "admin"


class RoleUserInStoreORM(BaseModel):
    __tablename__ = "role_user_in_store"
    __table_args__ = (UniqueConstraint("user_id", "store_id", name="unique_constraint_user_store"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    role: Mapped[RoleUserInStoreEnum] = mapped_column(
        SQLAlchemyEnum(RoleUserInStoreEnum, name="role_user_in_store_enum"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)

    store: Mapped["StoreORM"] = relationship(
        back_populates="roles", foreign_keys=[store_id], viewonly=True
    )

    user: Mapped["UserORM"] = relationship(
        back_populates="stores_roles", foreign_keys=[user_id], viewonly=True
    )


class UserORM(BaseModel):
    """
    Модель пользователя.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя. Первичный ключ.
        email (str): Уникальный email пользователя.
        hashed_password (str): Захешированный пароль пользователя.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column()
    company_role: Mapped[RoleUserInCompanyEnum] = mapped_column(
        SQLAlchemyEnum(RoleUserInCompanyEnum, name="company_role_enum"),
        server_default=RoleUserInCompanyEnum.member.value,
        nullable=False,
    )

    stores: Mapped[list["StoreORM"]] = relationship(
        back_populates="users", secondary="role_user_in_store", viewonly=True
    )

    stores_roles: Mapped["RoleUserInStoreORM"] = relationship(
        back_populates="user", foreign_keys="[RoleUserInStoreORM.user_id]", viewonly=True
    )

    notifications: Mapped[list["NotificationORM"]] = relationship(
        "NotificationORM", cascade="all, delete-orphan", passive_deletes=True
    )

    session: Mapped[list["SessionORM"]] = relationship(
        "SessionORM", cascade="all, delete-orphan", passive_deletes=True
    )


class SessionORM(BaseModel):
    """
    Модель сессии пользователя.

    Атрибуты:
        id (int): Уникальный идентификатор сессии. Первичный ключ.
        user_id (int): Внешний ключ на пользователя, которому принадлежит сессия.
        created_at (datetime): Дата и время создания сессии (UTC), устанавливается автоматически.
        expires_at (datetime): Дата и время истечения срока действия сессии (UTC), по умолчанию — через заданный период.
        device_id (uuid.UUID): Уникальный идентификатор устройства, с которого была создана сессия.
        refresh_tokens (str): Токен обновления, связанный с сессией.
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(column="users.id", name="sessions_user_id_fkey", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_expiration_refresh_token, index=True
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=False, nullable=False
    )
    refresh_token: Mapped[str | None] = mapped_column(index=True, nullable=True)
