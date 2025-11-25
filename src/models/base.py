from typing import ClassVar, Protocol

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, InstrumentedAttribute


class HasId(Protocol):
    """Подсказка для линтера: класс, у которого есть SQLA-атрибут id .where(model.id == id_)"""

    id: ClassVar[InstrumentedAttribute[int]]


class BaseModel(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
