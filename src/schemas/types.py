from enum import Enum
from typing import Annotated

from pydantic import Field, constr

Password = Annotated[
    str,
    Field(
        min_length=8,
        max_length=50,
        examples=["Ff7!54545"],
        description="Пароль от 8 до 50 символов. "
        "Должен содержать минимум 1 заглавную букву, "
        "1 строчную, 1 цифру и 1 спецсимвол (!@#$%^&* и т.д.)"
        "Например: Qwer123$",
    ),
]
ConfirmCode = Annotated[
    constr(min_length=6, max_length=6, pattern=r"^\d{6}$"),
    Field(..., description="6-значный код подтверждения"),
]


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class SortUnitBy(str, Enum):
    id = "id"
    title_ = "title"
    description = "description"
    quantity = "quantity"
    average_cost_price = "average_cost_price"
    retail_price = "retail_price"
    created_at = "created_at"


class UnitField(str, Enum):
    images = "images"
    transactions = "transactions"
    main_image = "main_image"


TitleStr = Annotated[str, Field(min_length=3, max_length=100)]
DescriptionStr = Annotated[str, Field(min_length=3, max_length=100)]
IDInt = Annotated[int, Field(ge=1, le=2147483647)]
S3Key = Annotated[str, Field(min_length=0, max_length=255, description="Ключ для s3 хранилища")]


class SortNotificationBy(str, Enum):
    id = "id"
    title_ = "title"
    is_read = "is_read"
    type = "type"
    created_at = "created_at"


class AppEnv(str, Enum):
    test = "test"
    local = "local"
    dev = "dev"
    prod = "prod"
