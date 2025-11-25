from src.exceptions.forbidden import (
    ApproveRegistrationForbiddenException,
    UpdateRoleInCompanyForbiddenException,
    SelfUpdateRoleInCompanyForbiddenException,
)
from src.exceptions.not_found import UserNotFoundException, ObjectNotFoundException
from src.schemas.users import UserDTO
from src.services.auths import AuthsService
from src.services.base import BaseService
from src.services.helpers.access_roles import (
    roles_can_approving_registration,
    roles_can_update_role_in_company,
    protected_roles_in_company,
)
from src.services.users import UsersService
from src.tasks.manager import task_manager
from src.models.users import RoleUserInCompanyEnum
from src.schemas.admins import ApproveRegistrationDTO, UpdateCompanyRoleDTO
from src.templates.constants import SUCCESSFUL_REGISTRATION_TEMPLATE


class AdminsService(BaseService):
    def check_company_role_can_approve_registration(
        self, user_role_in_company: RoleUserInCompanyEnum
    ):
        """
        :raise ApproveRegistrationForbiddenException: Если запрещено подтверждать регистрацию
        """
        if user_role_in_company not in roles_can_approving_registration:
            raise ApproveRegistrationForbiddenException

    async def approve_register_user(
        self, dto: ApproveRegistrationDTO, user_role_in_company: RoleUserInCompanyEnum
    ) -> str:
        """
        :raise ApproveRegistrationForbiddenException: Если запрещено подтверждать регистрацию.
        :raise UnconfirmedRegistrationNotFoundException: Если заявка на регистрацию не найдена.
        :raise UserAlreadyExistsException: Если пользователь с таким email уже существует
        """
        self.check_company_role_can_approve_registration(user_role_in_company)

        unconfirm_data = await AuthsService(cache=self.cache).check_get_unconfirmed_registration(
            str(dto.email)
        )

        if unconfirm_data.email_confirmed:
            await UsersService(db=self.db).add_user(dto=unconfirm_data.user)
            await self.cache.auths.delete_unconfirmed_registration(
                email=str(unconfirm_data.user.email)
            )
            await self.cache.commit()
            await self.db.commit()
            task_manager.send_msg_to_email(
                to_email=str(unconfirm_data.user.email),
                subject=SUCCESSFUL_REGISTRATION_TEMPLATE.subject,
                template_filename=SUCCESSFUL_REGISTRATION_TEMPLATE.template,
            )
            return "Пользователь зарегистрирован"
        else:
            unconfirm_data.admin_approved = True
            await self.cache.auths.update_unconfirmed_registration(dto=unconfirm_data)
            await self.cache.commit()
            return "Регистрация утверждена, ожидается подтверждение email"

    def check_company_role_can_update_role_in_company(
        self, user_role_in_company: RoleUserInCompanyEnum
    ):
        """
        :raise UpdateRoleInCompanyForbiddenException: Если запрещено изменять у пользователя роль в компании
        """
        if user_role_in_company not in roles_can_update_role_in_company:
            raise UpdateRoleInCompanyForbiddenException

    async def update_role_in_company(
        self,
        dto: UpdateCompanyRoleDTO,
        user_id: int,
        self_id: int,
        user_role_in_company: RoleUserInCompanyEnum,
    ) -> UserDTO:
        """
        :raise SelfUpdateRoleInCompanyForbiddenException: Если запрещено самому себе изменять роль в компании.
        :raise UpdateRoleInCompanyForbiddenException: Если запрещено изменять у пользователя роль в компании.
        :raise UserNotFoundException: Если пользователь не найден.
        """

        self.check_company_role_can_update_role_in_company(user_role_in_company)

        if user_id == self_id:
            raise SelfUpdateRoleInCompanyForbiddenException

        user = await UsersService(db=self.db, cache=self.cache).check_get_user_by_id(
            user_id=user_id, clear_cache=True
        )
        if user.company_role in protected_roles_in_company:
            raise UpdateRoleInCompanyForbiddenException

        try:
            update_user = await self.db.users.edit(dto=dto, id=user_id)
            await self.db.commit()
            return update_user
        except ObjectNotFoundException as exc:
            raise UserNotFoundException from exc
