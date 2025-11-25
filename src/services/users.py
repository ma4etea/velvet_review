from src.exceptions.base import ObjectAlreadyExistsException, UserAlreadyExistsException
from src.services.base import BaseService
from src.exceptions.not_found import (
    ObjectNotFoundException,
    UserSessionNotFoundException,
    UserNotFoundException,
    DeviceIDNotFoundException,
)
from src.schemas.users import UserDTO, AddUserDTO


class UsersService(BaseService):
    async def add_user(self, dto: AddUserDTO) -> None:
        """
        :raise UserAlreadyExistsException: Если пользователь с таким email уже существует
        """
        try:
            await self.db.users.add(dto)
        except ObjectAlreadyExistsException as exc:
            raise UserAlreadyExistsException from exc

    async def get_me(self, user_id: int) -> UserDTO:
        user = await self.check_get_user_by_id(user_id=user_id)
        return user

    async def logout_user(
        self, user_id: int, session_id: int, device_id: str | None = None
    ) -> None:
        """
        :raise DeviceIDNotFoundException
        :raise UserSessionNotFoundException
        """
        if not device_id:
            raise DeviceIDNotFoundException
        try:
            await self.db.user_sessions.delete(id=session_id, user_id=user_id, device_id=device_id)
        except ObjectNotFoundException as exc:
            raise UserSessionNotFoundException from exc
        await self.db.commit()

    async def check_get_user_by_id(self, user_id: int, clear_cache: bool = False) -> UserDTO:
        """
        Cached method: 15 minutes
        :raise UserNotFoundException: Если пользователь не найден.
        """
        user = await self.cache.users.get_one_or_none(obj_id=str(user_id))
        if not user:
            try:
                user = await self.db.users.get_one(id=user_id)
            except ObjectNotFoundException as exc:
                raise UserNotFoundException(user_id) from exc
            if not clear_cache:
                await self.cache.users.add(dto=user, obj_id=str(user_id), ttl=60 * 15)

        if clear_cache:
            await self.cache.users.delete(obj_id=str(user_id))
        await self.cache.commit()
        return user

    async def check_get_user_by_email(self, email: str) -> UserDTO:
        """
        :raise UserNotFoundException: Если пользователь с таким email не найден.
        """
        try:
            user: UserDTO = await self.db.users.get_one(email=email)
        except ObjectNotFoundException as exc:
            raise UserNotFoundException(email) from exc
        return user
