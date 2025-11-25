from src.repositories.cache.mappers.base import DataMapper
from src.schemas.auths import UnconfirmedRegistrationDTO, ForgotPasswordDTO
from src.schemas.users import UserDTO


class UnconfirmedRegistrationMapper(DataMapper[UnconfirmedRegistrationDTO]):
    schema = UnconfirmedRegistrationDTO


class ForgotPasswordMapper(DataMapper[ForgotPasswordDTO]):
    schema = ForgotPasswordDTO


class UsersMapper(DataMapper[UserDTO]):
    schema = UserDTO
