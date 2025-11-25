import uuid
from datetime import datetime

from pydantic import EmailStr, Field
from src.schemas.base import BaseSchema
from src.schemas.mixin import PasswordMixin
from src.schemas.types import Password, ConfirmCode
from src.schemas.users import AddUserDTO
from src.utils.time_manager import get_utc_now, get_expiration_refresh_token


class CredsUserDTO(PasswordMixin, BaseSchema):
    email: EmailStr
    password: Password


class UnconfirmedRegistrationDTO(BaseSchema):
    user: AddUserDTO
    confirm_code: ConfirmCode
    email_confirmed: bool = False
    admin_approved: bool = False
    timestamp: datetime = Field(default_factory=get_utc_now)


class ResendConfirmCodeDTO(BaseSchema):
    email: EmailStr


class ConfirmRegisterDTO(BaseSchema):
    email: EmailStr
    confirm_code: ConfirmCode


class ForgotPasswordDTO(BaseSchema):
    email: EmailStr
    attempts: int
    confirm_code: ConfirmCode


class ResetPasswordDTO(PasswordMixin, BaseSchema):
    email: EmailStr
    password: Password
    confirm_code: ConfirmCode


class ResetHashedPassword(BaseSchema):
    hashed_password: str


class TokensDTO(BaseSchema):
    access_token: str
    refresh_token: str
    device_id: uuid.UUID


class ResponseTokens(BaseSchema):
    tokens: TokensDTO


class AddSessionDTO(BaseSchema):
    user_id: int


class EditSessionDTO(BaseSchema):
    expires_at: datetime | None = Field(default_factory=get_expiration_refresh_token)
    device_id: uuid.UUID | None = None
    refresh_token: str | None = None


class UserSessionDTO(BaseSchema):
    id: int
    user_id: int
    created_at: datetime
    expires_at: datetime
    device_id: uuid.UUID
    refresh_token: str | None = None
