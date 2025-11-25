from src.exceptions.base import ObjectAlreadyExistsException, RoleUserInStoreAlreadyExistsException
from src.exceptions.conflict import StoreAlreadyExistsException
from src.exceptions.forbidden import (
    CreateStoreForbiddenException,
    AdminRoleModificationInStoreForbiddenException,
)
from src.exceptions.not_found import (
    ObjectNotFoundException,
    StoreNotFoundException,
    RoleUserInStoreNotFoundException,
)
from src.models.users import RoleUserInCompanyEnum
from src.schemas.admins import AssignUserToStoreDTO, UpdateUserRoleInStore
from src.schemas.stores import (
    AddStoreDTO,
    StoreDTO,
    AddRoleUserInStoreDTO,
    StoreWithRoleUsersDTO,
)
from src.services.base import BaseService
from src.services.helpers.access_roles import (
    roles_is_administrations,
)
from src.services.users import UsersService
from src.utils.cache.decorators import cache_service_method_by_id


class StoresService(BaseService):
    async def create_store(
        self, dto: AddStoreDTO, user_role_in_company: RoleUserInCompanyEnum
    ) -> StoreDTO:
        """
        :raise CreateStoreForbiddenException: Если запрещено создавать новый магазин.
        :raise StoreAlreadyExistsException: Если магазин с таким названием уже существует.
        """
        if user_role_in_company not in roles_is_administrations:
            raise CreateStoreForbiddenException

        try:
            store = await self.db.stores.add(dto)
        except ObjectAlreadyExistsException:
            raise StoreAlreadyExistsException
        await self.db.commit()
        return store

    @cache_service_method_by_id(return_type=StoreDTO, ttl=60 * 60 * 24)
    async def check_get_store_by_id(self, store_id: int) -> StoreDTO:
        """
        Cached method: 24 hours
        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        """
        try:
            store: StoreDTO = await self.db.stores.get_one(id=store_id)
        except ObjectNotFoundException as exc:
            raise StoreNotFoundException from exc
        return store

    async def assign_user_to_store(
        self, dto: AssignUserToStoreDTO, store_id: int
    ) -> StoreWithRoleUsersDTO:
        """
        :raise UserNotFoundException: Если пользователь не найден.
        :raise AdminRoleModificationInStoreForbiddenException: Если пользователь является администратором компании.
        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        :raise RoleUserInStoreAlreadyExistsException: Если пользователю уже назначена роль в этом магазине.
        """

        await self.check_user_and_not_is_admin(user_id=dto.user_id)

        await self.check_get_store_by_id(store_id=store_id)

        add_dto = AddRoleUserInStoreDTO(role=dto.role, user_id=dto.user_id, store_id=store_id)
        try:
            await self.db.role_user_in_store.add(dto=add_dto)
        except ObjectAlreadyExistsException:
            raise RoleUserInStoreAlreadyExistsException

        store_with_users = await self.db.stores.get_store_with_users(store_id=store_id)
        await self.db.commit()

        return store_with_users

    async def unassign_user_from_store(self, store_id: int, user_id: int) -> None:
        """
        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        :raise UserNotFoundException: Если пользователь не найден.
        :raise AdminRoleModificationInStoreForbiddenException: Если пользователь является администратором компании.
        :raise RoleUserInStoreNotFoundException: Если роль пользователя в для магазина не найдена.
        """
        await self.check_get_store_by_id(store_id=store_id)
        await self.check_user_and_not_is_admin(user_id=user_id)

        try:
            await self.db.role_user_in_store.delete(store_id=store_id, user_id=user_id)
        except ObjectNotFoundException:
            raise RoleUserInStoreNotFoundException

        await self.db.commit()

    async def update_role_user_in_store(
        self, store_id: int, user_id: int, dto: UpdateUserRoleInStore
    ) -> StoreWithRoleUsersDTO:
        """
        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        :raise UserNotFoundException: Если пользователь не найден.
        :raise AdminRoleModificationInStoreForbiddenException: Если пользователь является администратором компании.
        :raise RoleUserInStoreNotFoundException: Если роль пользователя в для магазина не найдена.
        """
        await self.check_get_store_by_id(store_id=store_id)
        await self.check_user_and_not_is_admin(user_id=user_id)

        try:
            await self.db.role_user_in_store.edit(dto=dto, store_id=store_id, user_id=user_id)
        except ObjectNotFoundException:
            raise RoleUserInStoreNotFoundException

        store_with_users = await self.db.stores.get_store_with_users(store_id=store_id)
        await self.db.commit()

        return store_with_users

    async def check_user_and_not_is_admin(self, user_id: int):
        """
        Need to initialize *cache*.
        :raise UserNotFoundException: Если пользователь не найден.
        :raise AdminRoleModificationInStoreForbiddenException: Если пользователь является администратором компании.
        """
        user = await UsersService(db=self.db, cache=self.cache).check_get_user_by_id(
            user_id=user_id
        )
        if user.company_role in roles_is_administrations:
            raise AdminRoleModificationInStoreForbiddenException

    async def get_store_with_users(self, store_id: int) -> StoreWithRoleUsersDTO:
        """
        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        """
        try:
            store_with_users = await self.db.stores.get_store_with_users(store_id=store_id)
        except ObjectNotFoundException as exc:
            raise StoreNotFoundException from exc
        return store_with_users
