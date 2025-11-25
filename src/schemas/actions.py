from datetime import datetime
from typing import Annotated, Union, Self

from pydantic import Field, model_validator

from src.models.actions import ActionEnum
from src.routers.http_exceptions.base import (
    UnitIdsDuplicateHTTPException,
)
from src.schemas.base import BaseSchema, PaginationItems
from src.schemas.query import PaginationQuery
from src.schemas.types import IDInt
from src.schemas.unit_images import UnitImageDTO

ActionFilter = Annotated[
    ActionEnum | None,
    Field(None, description="Фильтры для действий: опционально."),
]


class ActionsQuery(PaginationQuery):
    search_term: ActionFilter
    store_id: Annotated[
        IDInt | None,
        Field(
            None,
            description="Получить транзакции конкретного магазина по id. Если не указано то всех.",
        ),
    ]


class SalesTransaction(BaseSchema):
    unit_id: Annotated[int, Field(ge=1)]
    quantity_delta: Annotated[float, Field(ge=0.01)]
    discount_price: Annotated[float, Field(ge=0.01)]


class AddStockTransaction(BaseSchema):
    unit_id: Annotated[int, Field(ge=1)]
    quantity_delta: Annotated[float, Field(ge=0.01)]
    cost_price: Annotated[float, Field(ge=0.01)]
    retail_price: Annotated[float, Field(ge=0.01)]


class SalesReturnTransaction(BaseSchema):
    unit_id: Annotated[int, Field(ge=1)]
    quantity_delta: Annotated[float, Field(ge=0.01)]
    discount_price: Annotated[float, Field(ge=0.01)]


class WriteOffTransaction(BaseSchema):
    unit_id: Annotated[int, Field(ge=1)]
    quantity_delta: Annotated[float, Field(ge=0.01)]


class NewPriceTransaction(BaseSchema):
    unit_id: Annotated[int, Field(ge=1)]
    retail_price: Annotated[float, Field(ge=0.01)]


class StockReturnTransaction(BaseSchema):
    unit_id: Annotated[int, Field(ge=1)]
    quantity_delta: Annotated[float, Field(ge=0.01)]
    cost_price: Annotated[float, Field(ge=0.01)]


# class AddAction(BaseSchema):
#     quantity_delta: Annotated[float | None, Field(None, ge=0.01)]
#     cost_price: Annotated[float | None, Field(None, ge=0.01)]
#     retail_price: Annotated[float | None, Field(None, ge=0.01)]
#     discount_price: Annotated[float | None, Field(None, ge=0.01)]
#     unit_id: Annotated[int, Field(ge=1)]


TransactionUnion = Union[
    # AddAction,
    SalesTransaction,
    AddStockTransaction,
    SalesReturnTransaction,
    WriteOffTransaction,
    NewPriceTransaction,
    StockReturnTransaction,
]


class AddActionDTO(BaseSchema):
    transactions: list[TransactionUnion]
    store_id: IDInt
    action: ActionEnum

    @model_validator(mode="after")
    def validate_transaction_fields(self) -> Self:
        unit_ids = {transaction.unit_id for transaction in self.transactions}
        if len(unit_ids) != len(self.transactions):
            raise UnitIdsDuplicateHTTPException

        transaction_model_map = {
            "sales": SalesTransaction,
            "addStock": AddStockTransaction,
            "salesReturn": SalesReturnTransaction,
            "writeOff": WriteOffTransaction,
            "newPrice": NewPriceTransaction,
            "stockReturn": StockReturnTransaction,
        }

        schema = transaction_model_map[self.action]

        self.transactions = [
            schema.model_validate(tx, from_attributes=True) for tx in self.transactions
        ]

        return self


class AddActionTransactionToDbDTO(BaseSchema):
    quantity_delta: float | None
    cost_price: float | None
    retail_price: float | None
    previous_retail_price: float | None
    discount_price: float | None
    action: ActionEnum
    unit_id: int
    user_id: int
    action_id: int
    store_id: int


class ActionTransactionDTO(BaseSchema):
    id: int
    quantity_delta: float | None
    cost_price: float | None
    retail_price: float | None
    discount_price: float | None
    action: ActionEnum
    created_at: datetime


class ActionTransactionWithUnitDTO(ActionTransactionDTO):
    class UnitForTransaction(BaseSchema):
        id: int
        title: str
        description: str
        main_image: UnitImageDTO | None

    unit: UnitForTransaction


class AddActionToDbDTO(BaseSchema):
    action: ActionEnum


class ActionIdDTO(BaseSchema):
    id: int


class ActionDTO(ActionIdDTO):
    title: ActionEnum
    created_at: datetime
    store_id: int


class ActionResponse(BaseSchema):
    action: ActionIdDTO


class UnitTitle(BaseSchema):
    unit_id: int
    title: str


class ActionWithUnitsTransactionsDTO(BaseSchema):
    id: int
    title: ActionEnum
    created_at: datetime
    store_id: int
    store_title: str
    transactions: list[UnitTitle]


class ActionWithTransactionsDTO(ActionDTO):
    transactions: list[ActionTransactionWithUnitDTO]


class ActionWithUnitsResponse(BaseSchema):
    action: ActionWithTransactionsDTO


class ActionsWithUnitsResponse(BaseSchema):
    actions: PaginationItems[ActionWithUnitsTransactionsDTO]
