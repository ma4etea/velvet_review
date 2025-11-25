from src.exceptions.not_found import ObjectNotFoundException
from src.repositories.cache.mappers.mappers import (
    UnconfirmedRegistrationMapper,
    ForgotPasswordMapper,
)
from src.repositories.cache.base import BaseRepository
from src.repositories.cache.space_name import (
    space_name_unconfirmed_registration,
    space_name_cooldown_resend_confirm_code,
    space_name_forgot_password,
    space_name_cooldown_forgot_password,
)
from src.schemas.auths import UnconfirmedRegistrationDTO, ForgotPasswordDTO
from src.schemas.base import BaseSchema


class AuthsRepository(BaseRepository[BaseSchema]):
    async def add_unconfirmed_registration(self, dto: UnconfirmedRegistrationDTO, ttl: int):
        result = await self.adapter.set(
            key=space_name_unconfirmed_registration(str(dto.user.email)),
            value=UnconfirmedRegistrationMapper.to_cache(dto),
            ttl=ttl,
        )
        return result

    async def update_unconfirmed_registration(self, dto: UnconfirmedRegistrationDTO):
        """
        :raise ObjectNotFoundException:
        """
        key = space_name_unconfirmed_registration(str(dto.user.email))
        ttl = await self.adapter.get_ttl(key)
        if ttl == -2:
            raise ObjectNotFoundException

        result = await self.adapter.set(
            key=key, value=UnconfirmedRegistrationMapper.to_cache(dto), ttl=ttl if ttl > 0 else None
        )
        return result

    async def get_unconfirmed_registration(self, email: str) -> UnconfirmedRegistrationDTO:
        key = space_name_unconfirmed_registration(str(email))
        result = await self.adapter.get_one_or_none(key=key)
        if result is None:
            raise ObjectNotFoundException(key)
        return UnconfirmedRegistrationMapper.to_domain(result)

    async def check_unconfirmed_registration(self, email: str) -> bool:
        return await self.adapter.check_one(key=space_name_unconfirmed_registration(str(email)))

    async def delete_unconfirmed_registration(self, email: str) -> None:
        await self.adapter.delete_one(key=space_name_unconfirmed_registration(str(email)))

    async def add_cooldown_resend_confirm_code(self, email: str, ttl: int) -> bool:
        result = await self.adapter.set(key=space_name_cooldown_resend_confirm_code(email), ttl=ttl)
        return result

    async def check_cooldown_resend_confirm_code(self, email: str) -> bool:
        result = await self.adapter.check_one(key=space_name_cooldown_resend_confirm_code(email))
        return result

    async def delete_cooldown_resend_confirm_code(self, email: str) -> None:
        await self.adapter.delete_one(key=space_name_cooldown_resend_confirm_code(email))

    async def add_forgot_password(self, dto: ForgotPasswordDTO, ttl: int):
        result = await self.adapter.set(
            key=space_name_forgot_password(str(dto.email)),
            value=ForgotPasswordMapper.to_cache(dto),
            ttl=ttl,
        )
        return result

    async def get_forgot_password_or_none(self, email: str) -> ForgotPasswordDTO | None:
        result = await self.adapter.get_one_or_none(key=space_name_forgot_password(email))
        if result is None:
            return result
        return ForgotPasswordMapper.to_domain(result)

    async def delete_forgot_password(self, email: str) -> None:
        await self.adapter.delete_one(key=space_name_forgot_password(email))

    async def add_cooldown_forgot_password(self, email: str, ttl: int) -> bool:
        result = await self.adapter.set(key=space_name_cooldown_forgot_password(email), ttl=ttl)
        return result

    async def check_cooldown_forgot_password(self, email: str) -> bool:
        """Проверяет cooldown, если есть то True"""
        result = await self.adapter.check_one(key=space_name_cooldown_forgot_password(email))
        return result
