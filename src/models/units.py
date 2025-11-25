import typing

from sqlalchemy import Enum as SQLAlchemyEnum, ForeignKey
from enum import Enum

from sqlalchemy import String, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from src.models.base import BaseModel

if typing.TYPE_CHECKING:
    from src.models.users import UserORM, RoleUserInStoreORM
    from src.models.actions import ActionTransactionOrm


class UnitOfMeasurementEnum(str, Enum):
    """Единицы измерения товара: pieces, meters"""

    pieces = "pieces"
    meters = "meters"


class UnitORM(BaseModel):
    """
    Модель SQLAlchemy для представления товарной единицы (unit) на складе или в магазине.

    Атрибуты:
        id (int): Уникальный идентификатор единицы. Первичный ключ.
        name (str): Название единицы товара.
        description (str): Описание товара. По умолчанию — пустая строка.
        measurement(UnitOfMeasurement): Единицы измерения товара: pieces, meters
        quantity (float): Количество доступного товара. По умолчанию — 0.
        average_cost_price (float): Средняя себестоимость товара. По умолчанию — 0.
        retail_price (float): Розничная цена товара. По умолчанию — 0.
        keys_image (list[str]): Список ключей/идентификаторов изображений товара. По умолчанию пустой список.
        created_at (datetime): Дата и время создания записи (UTC). Устанавливается автоматически на уровне БД.
    """

    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(String(100), default="")
    measurement: Mapped[UnitOfMeasurementEnum] = mapped_column(
        SQLAlchemyEnum(UnitOfMeasurementEnum, name="unit_of_measurement_enum"),
        server_default=UnitOfMeasurementEnum.pieces.value,
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column(default=0)
    average_cost_price: Mapped[float] = mapped_column(default=0)
    retail_price: Mapped[float] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)

    main_image_id: Mapped[int] = mapped_column(ForeignKey("unit_images.id"), nullable=True)

    transactions: Mapped[list["ActionTransactionOrm"]] = relationship(back_populates="unit")
    images: Mapped[list["UnitImageORM"]] = relationship(
        back_populates="unit", foreign_keys="UnitImageORM.unit_id", passive_deletes=True
    )

    main_image: Mapped["UnitImageORM"] = relationship(
        back_populates="unit", foreign_keys=[main_image_id]
    )


class StoreORM(BaseModel):
    __tablename__ = "stores"
    """
    Торговая точка или склад, unit может иметь только один store.
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    users: Mapped[list["UserORM"]] = relationship(
        back_populates="stores", secondary="role_user_in_store", viewonly=True
    )
    roles: Mapped[list["RoleUserInStoreORM"]] = relationship(
        back_populates="store", foreign_keys="[RoleUserInStoreORM.store_id]", viewonly=True
    )


class UnitImageStatusEnum(str, Enum):
    """Состояние обработки изображения для единицы товара (unit)."""

    pending = "pending"
    done = "done"
    error = "error"


class UnitImageORM(BaseModel):
    __tablename__ = "unit_images"
    # __table_args__ = (CheckConstraint('image_order BETWEEN 1 AND 10', name='check_image_order_range'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), index=True)
    # image_order: Mapped[int] = mapped_column(Integer, nullable=False)
    key_100: Mapped[str] = mapped_column(String(255), nullable=True)
    key_300: Mapped[str] = mapped_column(String(255), nullable=True)
    key_1280: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[UnitImageStatusEnum] = mapped_column(
        SQLAlchemyEnum(UnitImageStatusEnum, name="unit_image_status"),
        server_default=UnitImageStatusEnum.pending.value,
        nullable=False,
    )

    unit: Mapped["UnitORM"] = relationship(back_populates="images", foreign_keys=[unit_id])
