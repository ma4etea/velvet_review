from typing import Annotated

from pydantic import Field

from src.schemas.base import BaseSchemaOrigin
from src.schemas.types import UnitField, SortOrder, SortUnitBy, IDInt, SortNotificationBy


class PaginationQuery(BaseSchemaOrigin):
    """
    - Primary key в postgres <= 2147483647 поэтому offset такой же.
    - Наследование от `BaseSchemaOrigin` потому что нужен `snake_case` для query параметров.
    """

    offset: Annotated[int, Field(0, ge=0, le=2147483647, examples=[1])]
    limit: Annotated[int, Field(50, ge=1, le=50, examples=[50])]


class GetUnitQuery(BaseSchemaOrigin):
    field: Annotated[set[UnitField] | None, Field(None, description="Получить дополнительные поля")]


class UnitsQuery(PaginationQuery):
    search_term: Annotated[
        str | None,
        Field(
            default=None,
            min_length=0,
            max_length=20,
            description='Фильтр при запросе, любая строка например: "новый"',
        ),
    ]
    store_id: Annotated[IDInt | None, Field(None, description="Товары только одного магазина")]
    sort_order: Annotated[
        SortOrder,
        Field(SortOrder.desc, description="Порядок сортировки: desk по убываю, asc по возрастанию"),
    ]
    sort_by: Annotated[SortUnitBy, Field(SortUnitBy.id, description="Поле сортировки")]


class NotificationsQuery(PaginationQuery):
    sort_order: Annotated[
        SortOrder,
        Field(SortOrder.desc, description="Порядок сортировки: desk по убываю, asc по возрастанию"),
    ]
    sort_by: Annotated[
        SortNotificationBy, Field(SortNotificationBy.id, description="Поле сортировки")
    ]
