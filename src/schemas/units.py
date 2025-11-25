from datetime import datetime
from typing import Annotated

from pydantic import Field, model_validator

from src.models.actions import ActionEnum
from src.models.units import UnitOfMeasurementEnum
from src.routers.http_exceptions.base import (
    PatchFieldValidationHTTPException,
    PatchUnitFieldValidationHTTPException,
)
from src.schemas.base import BaseSchema
from src.schemas.types import IDInt, TitleStr, DescriptionStr
from src.schemas.unit_images import UnitImageDTO

# MeasurementLiteral = Literal[*[e.value for e in UnitOfMeasurement]]
Measurement = Annotated[
    UnitOfMeasurementEnum,
    Field(description="Единицы измерения"),
]


class AddUnitDTO(BaseSchema):
    title: Annotated[str, Field(min_length=3, max_length=100)]
    description: Annotated[str, Field(max_length=100)]
    measurement: Measurement
    store_id: Annotated[
        int,
        Field(
            ge=1, description="Id магазина в котором будет создан товар, привязка товара к магазину"
        ),
    ]


class EditUnitDTO(BaseSchema):
    """main_image_id может быть None"""

    title: TitleStr | None = None
    description: DescriptionStr | None = None
    main_image_id: IDInt | None = None
    measurement: Measurement | None = None

    @model_validator(mode="after")
    def at_least_one_non_null(self):
        data = self.model_dump(exclude_unset=True)

        if not data:
            raise PatchFieldValidationHTTPException

        for key, value in data.items():
            if not value and key != "main_image_id":
                raise PatchUnitFieldValidationHTTPException
        return self


class Action(BaseSchema):
    id: int
    quantity_delta: float | None
    cost_price: float | None
    retail_price: float | None
    discount_price: float | None
    action: ActionEnum
    created_at: datetime


class UnitDTO(BaseSchema):
    id: int
    title: str
    description: str
    measurement: Measurement
    store_id: int
    quantity: float
    average_cost_price: float
    retail_price: float
    main_image_id: int | None
    created_at: datetime


class UnitWithMainImageDTO(UnitDTO):
    main_image: UnitImageDTO | None


class UnitResponse(BaseSchema):
    unit: UnitDTO


class UnitWithFieldsDTO(UnitDTO):
    transactions: list[Action] | None = None
    images: list[UnitImageDTO] | None = None
    main_image: UnitImageDTO | None = None


class UnitWithFieldsResponse(BaseSchema):
    unit: UnitWithFieldsDTO


class UnitsResponse(BaseSchema):
    units: list[UnitDTO]


class UnitsWithMainImageResponse(BaseSchema):
    units: list[UnitWithMainImageDTO]
