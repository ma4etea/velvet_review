from enum import Enum

from pydantic import EmailStr

from src.models.users import RoleUserInStoreEnum
from src.schemas.base import BaseSchema
from src.schemas.stores import StoreWithRoleUsersDTO
from src.schemas.types import IDInt
from src.schemas.users import UserDTO


class ApproveRegistrationDTO(BaseSchema):
    email: EmailStr


class UpdateRoleUserInCompanyEnum(str, Enum):
    member = "member"
    admin = "admin"


class UpdateCompanyRoleDTO(BaseSchema):
    company_role: UpdateRoleUserInCompanyEnum


class CompanyRoleResponse(BaseSchema):
    user: UserDTO


class AssignUserToStoreDTO(BaseSchema):
    user_id: IDInt
    role: RoleUserInStoreEnum


class UpdateUserRoleInStore(BaseSchema):
    role: RoleUserInStoreEnum


class StoreWithUsersResponse(BaseSchema):
    store: StoreWithRoleUsersDTO
