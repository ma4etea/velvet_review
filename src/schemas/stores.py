from typing import Annotated

from pydantic import Field

from src.models.users import RoleUserInStoreEnum
from src.schemas.base import BaseSchema
from src.schemas.users import UserDTO


class AddStoreDTO(BaseSchema):
    title: Annotated[
        str,
        Field(
            min_length=3, max_length=50, description="Название магазина(торговой точки или склада)"
        ),
    ]


class StoreDTO(AddStoreDTO):
    id: int


class StoreResponse(BaseSchema):
    store: StoreDTO


class AddRoleUserInStoreDTO(BaseSchema):
    role: RoleUserInStoreEnum
    user_id: int
    store_id: int


class RoleUserInStoreDTO(AddRoleUserInStoreDTO):
    id: int


class RoleWithUser(BaseSchema):
    id: int
    role: RoleUserInStoreEnum
    user: UserDTO


class StoreWithRoleUsersDTO(StoreDTO):
    roles: list[RoleWithUser]
