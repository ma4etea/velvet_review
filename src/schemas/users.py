from pydantic import EmailStr

from src.models.users import RoleUserInCompanyEnum
from src.schemas.base import BaseSchema


class AddUserDTO(BaseSchema):
    email: EmailStr
    hashed_password: str
    company_role: RoleUserInCompanyEnum


class UserDTO(BaseSchema):
    id: int
    email: EmailStr
    company_role: RoleUserInCompanyEnum


class UserResponse(BaseSchema):
    user: UserDTO


class UserWithHashedPasswordDTO(UserDTO):
    hashed_password: str
