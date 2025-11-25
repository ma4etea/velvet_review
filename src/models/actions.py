import typing
from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey
from sqlalchemy import func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if typing.TYPE_CHECKING:
    from src.models.units import UnitORM


class ActionEnum(str, Enum):
    """
    Перечисление действий, которые можно совершить над товаром.

    Значения:
        sales: Продажа товара.
        addStock: Пополнение склада.
        salesReturn: Возврат товара от клиента.
        writeOff: Списание товара.
        newPrice: Установка новой цены.
        stockReturn: Возврат товара поставщику.
    """

    sales = "sales"
    addStock = "addStock"
    salesReturn = "salesReturn"
    writeOff = "writeOff"
    newPrice = "newPrice"
    stockReturn = "stockReturn"


class ActionTransactionOrm(BaseModel):
    """
    Модель транзакции, фиксирующая операцию над товаром.

    Если нужно получить действие (action) вместе с соответствующим списком транзакций,
    можно получить все транзакции из базы и сгруппировать их по полю action_id.
    Название и дату создания взять из любой action и created_at группы.

    Атрибуты:
        id (int): Уникальный идентификатор транзакции.
        quantity_delta (Optional[float]): Изменение количества товара (плюс или минус). Может быть None, если не применимо.
        cost_price (Optional[float]): Новая себестоимость товара после операции. Может быть None.
        retail_price (Optional[float]): Новая розничная цена товара после операции. Может быть None.
        discount_price (Optional[float]): Новая цена со скидкой после операции. Может быть None.
        action (ActionEnum): Тип действия, совершённого над товаром (например, продажа, списание и т.д.).
        created_at (datetime): Время создания записи транзакции (UTC), устанавливается автоматически.
        unit_id (int): Внешний ключ на товар.
        user_id (int): Внешний ключ на пользователя, совершившего действие.
        action_id (int): Внешний ключ на действие(нужно для привязки всех транзакций к действию).
        store_id (int): Внешний ключ на магазин(склад), в котором произошла транзакция.
    """

    __tablename__ = "actions_transactions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    quantity_delta: Mapped[float | None] = mapped_column(nullable=True)
    cost_price: Mapped[float | None] = mapped_column(nullable=True)
    retail_price: Mapped[float | None] = mapped_column(nullable=True)
    previous_retail_price: Mapped[float | None] = mapped_column(nullable=True)
    discount_price: Mapped[float | None] = mapped_column(nullable=True)

    action: Mapped[ActionEnum] = mapped_column(
        SQLAlchemyEnum(ActionEnum, name="action_enum"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action_id: Mapped[int] = mapped_column(ForeignKey("actions.id"), index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)

    unit: Mapped["UnitORM"] = relationship(back_populates="transactions")
    action_: Mapped["ActionOrm"] = relationship(back_populates="transactions")


class ActionOrm(BaseModel):
    __tablename__ = "actions"
    """
    Действие, нужно для привязки транзакций к одному действия например: sales нескольких товаров в одном действии.
    """
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[ActionEnum] = mapped_column(
        SQLAlchemyEnum(ActionEnum, name="action_enum"), index=True
    )
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["ActionTransactionOrm"]] = relationship(back_populates="action_")
