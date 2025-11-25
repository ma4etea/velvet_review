from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from src.exceptions.not_found import ObjectNotFoundException
from src.logging_config import logger
from src.models.users import UserORM, SessionORM, RoleUserInCompanyEnum
from src.repositories.db.base import BaseRepository
from src.repositories.db.mappers.mappers import UsersDataMapper, SessionsDataMapper
from src.schemas.auths import UserSessionDTO
from src.schemas.users import UserWithHashedPasswordDTO, UserDTO
from src.utils.logger_utils import exc_log_string


class UsersRepository(BaseRepository[UserORM, UserDTO]):
    model = UserORM
    mapper = UsersDataMapper

    async def get_user_with_hashed_password(self, email: str):
        query = select(self.model).filter_by(email=email)
        try:
            result = await self.session.execute(query)
            model = result.scalar_one()
            return UserWithHashedPasswordDTO.model_validate(model, from_attributes=True)
        except NoResultFound as exc:
            logger.error(exc_log_string(exc))
            raise ObjectNotFoundException from exc

    async def get_users_by_company_roles(
        self, *company_roles: RoleUserInCompanyEnum
    ) -> list[UserDTO]:
        result = await self.get_all(self.model.company_role.in_(company_roles))
        return result


class SessionsRepository(BaseRepository[SessionORM, UserSessionDTO]):
    model = SessionORM
    mapper = SessionsDataMapper
