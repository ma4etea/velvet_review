from datetime import timedelta

from src.models.notifications import NotificationType, NotificationTargetObject
from src.services.helpers.access_roles import roles_can_approving_registration
from src.services.users import UsersService
from src.tasks.manager import task_manager
from src.config import settings
from src.adapters.redis_adapter import redis_adapter
from src.exceptions.base import (
    UserAlreadyExistsException,
    InvalidPasswordException,
    ExpiredConfirmCodeException,
    InvalidConfirmCodeException,
    UnconfirmedRegistrationAlreadyExistsException,
    ResendLimitAlreadyExistsException,
    CooldownForgotAlreadyExistsException,
    DeviceMismatchException,
)
from src.exceptions.not_found import (
    ObjectNotFoundException,
    UserNotFoundException,
    UserSessionNotFoundException,
    UnconfirmedRegistrationNotFoundException,
    ForgotPasswordNotFoundException,
    UsersCanApprovingRegistrationNotFoundException,
    RefreshTokenNotFoundException,
)
from src.logging_config import logger
from src.models.users import RoleUserInCompanyEnum
from src.schemas.stores import RoleUserInStoreDTO
from src.schemas.users import AddUserDTO, UserDTO, UserWithHashedPasswordDTO
from src.schemas.notifications import AddNotificationDTO
from src.schemas.auths import (
    CredsUserDTO,
    UnconfirmedRegistrationDTO,
    ResendConfirmCodeDTO,
    ConfirmRegisterDTO,
    ForgotPasswordDTO,
    ResetPasswordDTO,
    ResetHashedPassword,
    TokensDTO,
    AddSessionDTO,
    EditSessionDTO,
    UserSessionDTO,
)
from src.services.base import BaseService
from src.templates.constants import (
    FORGOT_PASSWORD_TEMPLATE,
    CONFIRMATION_EMAIL_TEMPLATE,
    SUCCESSFUL_REGISTRATION_TEMPLATE,
)
from src.utils.time_manager import get_utc_now
from src.utils.tokens_manager import token_manager


class AuthsService(BaseService):
    async def register_user(self, creds: CredsUserDTO):
        """
        Создает заявку на регистрацию в кэше:
            - код подтверждения живет 10 минут
            - заявка с возможностью resend 24 часа
        :param creds: Регистрационные данные пользователя
        :raise UnconfirmedRegistrationAlreadyExistsException: Если существует неподтвержденная регистрация.
        :raise UserAlreadyExistsException: Если пользователь с таким email уже существует.
        """

        if await self.cache.auths.check_unconfirmed_registration(str(creds.email)):
            raise UnconfirmedRegistrationAlreadyExistsException

        user = await self.db.users.get_one_or_none(email=str(creds.email))
        if user:
            raise UserAlreadyExistsException

        total_users = await self.db.users.get_total()

        unregistered_user = AddUserDTO(
            email=creds.email,
            hashed_password=token_manager.hash_password(password=creds.password),
            company_role=RoleUserInCompanyEnum.owner
            if total_users == 0
            else RoleUserInCompanyEnum.member,
        )

        unconfirmed_registration = UnconfirmedRegistrationDTO(
            user=unregistered_user,
            confirm_code=token_manager.create_confirm_code(),
            admin_approved=True if total_users == 0 else False,
        )

        task_manager.send_msg_to_email(
            to_email=str(unconfirmed_registration.user.email),
            subject=CONFIRMATION_EMAIL_TEMPLATE.subject,
            template_filename=CONFIRMATION_EMAIL_TEMPLATE.template,
            code=unconfirmed_registration.confirm_code,
        )

        await self.cache.auths.add_unconfirmed_registration(
            dto=unconfirmed_registration, ttl=settings.UNCONFIRMED_REGISTRATION_EXPIRE_MINUTES * 60
        )

        await self.cache.auths.add_cooldown_resend_confirm_code(
            email=str(unconfirmed_registration.user.email), ttl=60
        )

        await self.cache.commit()

        if total_users != 0:
            users = await self.db.users.get_users_by_company_roles(
                *roles_can_approving_registration
            )
            if not users:
                raise UsersCanApprovingRegistrationNotFoundException

            notifications = [
                AddNotificationDTO(
                    title="Подтверждение добавление нового пользователя",
                    body=f"Регистрируется новый пользователь с email: {unconfirmed_registration.user.email}, "
                    f"требуется подтверждение регистрации от администратора",
                    user_id=user.id,
                    type=NotificationType.approves,
                    target_object=NotificationTargetObject.users,
                    target_key=str(unconfirmed_registration.user.email),
                )
                for user in users
            ]
            await self.db.notifications.add_bulk(*notifications)
            await self.db.commit()

    async def resend_confirm_code(self, dto: ResendConfirmCodeDTO) -> None:
        """
        Raises:
            UnconfirmedRegistrationNotFoundException: Если заявка на регистрацию не найдена
            ResendLimitAlreadyExistsException: Если лимит в редисе еще существует
        """
        if await self.cache.auths.check_cooldown_resend_confirm_code(str(dto.email)):
            raise ResendLimitAlreadyExistsException

        unconfirmed_registration = await self.check_get_unconfirmed_registration(str(dto.email))
        end_date = unconfirmed_registration.timestamp + timedelta(
            minutes=settings.UNCONFIRMED_REGISTRATION_EXPIRE_MINUTES
        )
        ttl = max(
            int((end_date - get_utc_now()).total_seconds()), 0
        )  # если прошло время — получаем 0
        if (
            ttl < 20
        ):  # Небольшое перекрытие. Если осталось меньше 20 секунд, то отменяем регистрацию.
            await redis_adapter.delete_one(str(unconfirmed_registration.user.email))
            raise UnconfirmedRegistrationNotFoundException

        unconfirmed_registration.confirm_code = token_manager.create_confirm_code()

        task_manager.send_msg_to_email(
            to_email=str(unconfirmed_registration.user.email),
            subject=CONFIRMATION_EMAIL_TEMPLATE.subject,
            template_filename=CONFIRMATION_EMAIL_TEMPLATE.template,
            code=unconfirmed_registration.confirm_code,
        )

        await self.cache.auths.add_unconfirmed_registration(dto=unconfirmed_registration, ttl=ttl)
        await self.cache.auths.add_cooldown_resend_confirm_code(
            email=str(unconfirmed_registration.user.email), ttl=60
        )
        await self.cache.commit()

    async def check_get_unconfirmed_registration(self, email: str) -> UnconfirmedRegistrationDTO:
        """
        Raises:
            UnconfirmedRegistrationNotFoundException: Если заявка на регистрацию не найдена
        """
        try:
            return await self.cache.auths.get_unconfirmed_registration(email)
        except ObjectNotFoundException:
            raise UnconfirmedRegistrationNotFoundException

    async def confirm_email(self, dto: ConfirmRegisterDTO) -> str:
        """
        :raise UnconfirmedRegistrationNotFoundException: Если заявка на регистрацию не найдена
        :raise ExpiredConfirmCodeException: Если код подтверждения истек
        :raise InvalidConfirmCodeException: Если код подтверждения не верный
        """
        unconfirm_data = await self.check_get_unconfirmed_registration(str(dto.email))
        expires_delta = timedelta(minutes=settings.CONFIRM_CODE_EXPIRE_MINUTES)
        if unconfirm_data.timestamp + expires_delta < get_utc_now():
            raise ExpiredConfirmCodeException

        if unconfirm_data.confirm_code != dto.confirm_code:
            raise InvalidConfirmCodeException

        if unconfirm_data.admin_approved:
            await UsersService(db=self.db).add_user(dto=unconfirm_data.user)

            logger.debug(str(unconfirm_data.user.email))
            await self.cache.auths.delete_cooldown_resend_confirm_code(
                email=str(unconfirm_data.user.email)
            )
            await self.cache.auths.delete_unconfirmed_registration(
                email=str(unconfirm_data.user.email)
            )

            logger.debug(self.cache.adapter.deleting_keys)
            await self.cache.commit()
            logger.debug(self.cache.adapter.deleting_keys)

            await self.db.commit()
            task_manager.send_msg_to_email(
                to_email=str(unconfirm_data.user.email),
                subject=SUCCESSFUL_REGISTRATION_TEMPLATE.subject,
                template_filename=SUCCESSFUL_REGISTRATION_TEMPLATE.template,
            )
            return "Пользователь зарегистрирован"
        else:
            unconfirm_data.email_confirmed = True
            await self.cache.auths.update_unconfirmed_registration(dto=unconfirm_data)
            await self.cache.commit()
            return "Email подтвержден, ожидайте подтверждение от администратора"

    async def forgot_password(self, dto: ResendConfirmCodeDTO) -> None:
        """
        :raise CooldownForgotAlreadyExistsException: Если ключ с cooldown-forgot--email в редисе еще существует
        :raise UserNotFoundException: Если пользователь с таким email не найден.
        """

        # проверяем есть ли cooldown
        if await self.cache.auths.check_cooldown_forgot_password(str(dto.email)):
            raise CooldownForgotAlreadyExistsException

        # Проверяем есть ли уже запрос на сброс пароля в кэше
        forgot_password = await self.cache.auths.get_forgot_password_or_none(email=str(dto.email))
        ttl = settings.FORGOT_PASSWORD_EXPIRE_MINUTES * 60
        if forgot_password is None:
            await UsersService(db=self.db).check_get_user_by_email(str(dto.email))

            forgot_password = ForgotPasswordDTO(
                email=dto.email, attempts=1, confirm_code=token_manager.create_confirm_code()
            )

            await self.cache.auths.add_forgot_password(dto=forgot_password, ttl=ttl)
            cooldown = 60

        else:

            def get_cooldown(attempt: int, base_delay: int = 30, max_cooldown: int = 600) -> int:
                """
                Создает экспоненциальную задержку, возвращает секунды.
                """
                return min(base_delay * 2**attempt, max_cooldown)

            forgot_password.attempts = forgot_password.attempts + 1
            forgot_password.confirm_code = token_manager.create_confirm_code()
            await self.cache.auths.add_forgot_password(dto=forgot_password, ttl=ttl)

            cooldown = get_cooldown(attempt=forgot_password.attempts)

        await self.cache.commit()

        # logger.debug(f"{forgot_password.attempts=}, {cooldown=}")

        await self.cache.auths.add_cooldown_forgot_password(email=str(dto.email), ttl=cooldown)
        task_manager.send_msg_to_email(
            to_email=str(forgot_password.email),
            subject=FORGOT_PASSWORD_TEMPLATE.subject,
            template_filename=FORGOT_PASSWORD_TEMPLATE.template,
            code=forgot_password.confirm_code,
        )

    async def reset_password(self, data: ResetPasswordDTO) -> None:
        """
        Raises:
            ForgotPasswordNotFoundException: Если заявка на сброс пароля не найдена
            InvalidConfirmCodeException: Если код подтверждения не верный
            UserNotFoundException: Пользователь не найден
        """
        forgot_password = await self.cache.auths.get_forgot_password_or_none(email=str(data.email))
        if forgot_password is None:
            raise ForgotPasswordNotFoundException
        else:
            if forgot_password.confirm_code != data.confirm_code:
                raise InvalidConfirmCodeException

            hashed_password = token_manager.hash_password(password=data.password)
            new_data_user = ResetHashedPassword(hashed_password=hashed_password)

            try:
                await self.db.users.edit(new_data_user, email=str(data.email))
            except ObjectNotFoundException as exc:
                raise UserNotFoundException from exc

        await self.cache.auths.delete_forgot_password(email=str(forgot_password.email))
        await self.cache.commit()
        await self.db.commit()

    async def login_user(self, creds: CredsUserDTO, device_id: str | None = None) -> TokensDTO:
        """
        :raise UserNotFoundException
        :raise InvalidPasswordException
        :raise UserSessionNotFoundException
        """
        try:
            user: UserWithHashedPasswordDTO = await self.db.users.get_user_with_hashed_password(
                email=creds.email
            )
        except ObjectNotFoundException as exc:
            raise UserNotFoundException(object_id=str(creds.email)) from exc

        if not token_manager.verify_password(creds.password, user.hashed_password):
            raise InvalidPasswordException

        if device_id:
            user_session = await self.db.user_sessions.get_one_or_none(
                user_id=user.id, device_id=device_id
            )
            if user_session is None:
                user_session = await self.db.user_sessions.add(AddSessionDTO(user_id=user.id))

        else:
            user_session = await self.db.user_sessions.add(AddSessionDTO(user_id=user.id))

        tokens = await self.create_tokens(user_session=user_session, user=user)
        await self.db.commit()

        return tokens

    async def refresh_user_tokens(self, session_id: int, device_id: str | None) -> TokensDTO:
        """
        :raise UserSessionNotFoundException: Если сессия пользователя не найдена
        :raise DeviceMismatchException: Если device_id не соответствует сессии
        """
        user_session = await self.check_get_user_session(session_id=session_id)

        if device_id is None or device_id != str(
            user_session.device_id
        ):  # Возможная попытка взлома
            await self.db.user_sessions.delete(id=session_id)
            await self.db.commit()
            raise DeviceMismatchException

        user = await UsersService(db=self.db, cache=self.cache).check_get_user_by_id(
            user_id=user_session.user_id
        )

        tokens = await self.create_tokens(user_session=user_session, user=user)
        await self.db.commit()

        return tokens

    async def create_tokens(self, user_session: UserSessionDTO, user: UserDTO) -> TokensDTO:
        try:
            roles_user_in_stores: list[
                RoleUserInStoreDTO
            ] = await self.db.role_user_in_store.get_all(user_id=user_session.user_id)
        except Exception:
            raise

        user_roles_in_stores_payload = {item.store_id: item.role for item in roles_user_in_stores}

        access_token = token_manager.create_access_token(
            user_id=user_session.user_id,
            company_role=user.company_role,
            stores_roles=user_roles_in_stores_payload,
        )
        refresh_token = token_manager.create_refresh_token(
            session_id=user_session.id, device_id=str(user_session.device_id)
        )
        user_session = await self.db.user_sessions.edit(
            EditSessionDTO(refresh_token=refresh_token), id=user_session.id, exclude_unset=True
        )

        if not user_session.refresh_token:
            raise RefreshTokenNotFoundException

        tokens = TokensDTO(
            access_token=access_token,
            refresh_token=user_session.refresh_token,
            device_id=user_session.device_id,
        )

        return tokens

    async def check_get_user_session(self, session_id: int) -> UserSessionDTO:
        """
        :raise UserSessionNotFoundException: Если сессия пользователя не найдена
        """
        try:
            user_session = await self.db.user_sessions.get_one(id=session_id)
        except ObjectNotFoundException as exc:
            raise UserSessionNotFoundException from exc
        return user_session
