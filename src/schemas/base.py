from datetime import datetime
from typing import TypeVar, Generic, List, Any, Sequence, Annotated

import inflection
from pydantic import BaseModel, Field, ConfigDict

from src.schemas.types import IDInt
from src.utils.time_manager import get_utc_now


class BaseSchemaOrigin(BaseModel):
    """Оригинальный pydantic"""


class BaseSchema(BaseSchemaOrigin):
    model_config = ConfigDict(
        # new_case extra="forbid", это выбросит pydantic_core._pydantic_core.ValidationError если переданы лишние поля
        from_attributes=True,
        alias_generator=lambda s: inflection.camelize(
            s, uppercase_first_letter=False
        ),  # Преобразует snake_case в camelCase
        populate_by_name=True,  # Позволяет использовать snake_case при входных данных
    )


class Meta(BaseSchema):
    timestamp: datetime = Field(default_factory=get_utc_now)


ResponseType = TypeVar("ResponseType", bound=BaseSchema)


class NullDataResponse(BaseSchema):
    message: str | None = None
    meta: Meta = Field(default_factory=Meta)


class StandardResponse(BaseSchema, Generic[ResponseType]):
    data: ResponseType
    message: str | None = None
    meta: Meta = Field(default_factory=Meta)


class ErrorResponse(BaseSchema):
    status_code: int
    detail: str
    meta: Meta = Field(default_factory=Meta)


class ValidationErrorItem(BaseSchema):
    loc: List[Any]
    msg: str
    type: str


class ValidationErrorResponse(BaseSchema):
    status_code: Annotated[int, Field(examples=[422])]
    detail: Sequence[ValidationErrorItem]
    meta: Meta = Field(default_factory=Meta)


class Pagination(BaseSchema):
    total: Annotated[IDInt, Field(examples=[100])]
    offset: Annotated[int, Field(ge=0, le=2147483647, examples=[1])]
    limit: Annotated[int, Field(ge=1, le=50, examples=[50])]


class PaginationItems(BaseSchema, Generic[ResponseType]):
    pagination: Pagination
    items: list[ResponseType]
