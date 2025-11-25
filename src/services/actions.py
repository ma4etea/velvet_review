from collections import defaultdict, Counter
from typing import cast

from src.exceptions.base import UnitOutOfStockException
from src.exceptions.conflict import IdDuplicateException, UnitBelongAnotherStoreException
from src.exceptions.forbidden import (
    ActionAccessForbiddenException,
    StoreAccessForbiddenException,
    AllStoresAccessForbiddenException,
)
from src.exceptions.not_found import (
    UnitNotFoundException,
    ObjectNotFoundException,
    ActionNotFoundException,
)
from src.models.actions import ActionEnum
from src.models.users import RoleUserInStoreEnum, RoleUserInCompanyEnum
from src.schemas.actions import (
    ActionWithTransactionsDTO,
    ActionWithUnitsTransactionsDTO,
    AddActionDTO,
    ActionIdDTO,
    ActionFilter,
    ActionDTO,
    SalesTransaction,
    WriteOffTransaction,
    StockReturnTransaction,
)
from src.schemas.base import Pagination
from src.schemas.units import UnitDTO
from src.services.base import BaseService
from src.services.helpers.access_roles import (
    roles_can_sales,
    roles_can_add_stock,
    roles_can_sales_return,
    roles_can_write_off,
    roles_can_new_price,
    roles_can_stock_return,
    roles_can_read_action_in_store,
    roles_is_administrations,
)
from src.services.stores import StoresService
from src.utils.cache.decorators import cache_service_method_by_id


class ActionsService(BaseService):
    async def add_action(
        self,
        user_id: int,
        dto: AddActionDTO,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        user_role_in_company: RoleUserInCompanyEnum,
    ) -> ActionIdDTO:
        """
        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        :raise ActionAccessForbiddenException: Если нет прав на совершение действия.
        :raise UnitReadInStoreForbiddenException: Если передан хотя бы один товар принадлежащий другому store.
        :raise IdDuplicateException: Если переданы дубликаты `unit_id`
        :raise UnitNotFoundException: Если хотя бы один товар с указанными ID не найдены.
        :raise UnitBelongAnotherStoreException: Если передан хотя бы один товар принадлежащий другому store.
        :raise UnitOutOfStockException: Если *вычитаемое* количество товара больше доступного.
        """

        def check_role_in_store(roles_can: set[RoleUserInStoreEnum]):
            """Проверка роли доступа к действию"""
            if user_role_in_company not in roles_is_administrations:
                role_in_store = user_roles_in_stores.get(dto.store_id)
                if role_in_store not in roles_can:
                    raise ActionAccessForbiddenException(dto.action)

        async def check_units_exist_and_belong_store(
            check_ids: tuple[int, ...], store_id: int
        ) -> list[UnitDTO]:
            """
            Проверяет:
                - что переданы только уникальные `unit_id`
                - все `unit_id` существуют
                - принадлежат переданному `store_id`
            :raise IdDuplicateException: Если переданы дубликаты `unit_id`
            :raise UnitNotFoundException: Если хотя бы один товар с указанными ID не найдены.
            :raise UnitBelongAnotherStoreException: Если передан хотя бы один товар принадлежащий другому store.
            """

            # проверка на дубликаты
            unique_ids = set(check_ids)
            if len(check_ids) != len(unique_ids):
                duplicates = [i for i, count in Counter(check_ids).items() if count > 1]
                raise IdDuplicateException(", ".join(map(str, duplicates)))

            units = await self.db.units.get_all_by_ids(*unique_ids)

            existing_ids: set[int] = set()
            foreign_ids: set[int] = set()
            for unit in units:
                existing_ids.add(unit.id)
                if unit.store_id != store_id:
                    foreign_ids.add(unit.id)

            missing_ids = unique_ids - existing_ids
            if missing_ids:
                raise UnitNotFoundException(", ".join(map(str, missing_ids)))

            if foreign_ids:
                raise UnitBelongAnotherStoreException(", ".join(map(str, foreign_ids)))

            return units

        def check_quantity_positive(
            check_units: list[UnitDTO],
            transactions: tuple[
                SalesTransaction | WriteOffTransaction | StockReturnTransaction, ...
            ],
        ):
            """проверяет что количество товара не становится меньше 0"""
            quantity_delta_map: defaultdict[int, float] = defaultdict(float)
            for _transaction in transactions:
                quantity_delta_map[_transaction.unit_id] += _transaction.quantity_delta
            for _unit in check_units:
                remaining_quantity = _unit.quantity - quantity_delta_map[_unit.id]
                if remaining_quantity < 0:
                    raise UnitOutOfStockException

        unit_ids = tuple(transaction.unit_id for transaction in dto.transactions)

        match dto.action:
            case ActionEnum.addStock:
                check_role_in_store(roles_can_add_stock)
                await check_units_exist_and_belong_store(check_ids=unit_ids, store_id=dto.store_id)
                action_id = await self.db.actions_transactions.add_stock(user_id=user_id, data=dto)

            case ActionEnum.sales:
                check_role_in_store(roles_can_sales)
                units = await check_units_exist_and_belong_store(
                    check_ids=unit_ids, store_id=dto.store_id
                )
                sales_transactions: list[SalesTransaction] = cast(
                    list[SalesTransaction], dto.transactions
                )
                check_quantity_positive(check_units=units, transactions=tuple(sales_transactions))
                action_id = await self.db.actions_transactions.sales(
                    user_id=user_id,
                    store_id=dto.store_id,
                    action=dto.action,
                    sales_transactions=sales_transactions,
                )

            case ActionEnum.salesReturn:
                check_role_in_store(roles_can_sales_return)
                await check_units_exist_and_belong_store(check_ids=unit_ids, store_id=dto.store_id)
                action_id = await self.db.actions_transactions.sales_return(
                    user_id=user_id, data=dto
                )

            case ActionEnum.writeOff:
                check_role_in_store(roles_can_write_off)
                units = await check_units_exist_and_belong_store(
                    check_ids=unit_ids, store_id=dto.store_id
                )
                write_off_transactions: list[WriteOffTransaction] = cast(
                    list[WriteOffTransaction], dto.transactions
                )
                check_quantity_positive(
                    check_units=units, transactions=tuple(write_off_transactions)
                )
                action_id = await self.db.actions_transactions.write_off(user_id=user_id, data=dto)

            case ActionEnum.newPrice:
                check_role_in_store(roles_can_new_price)
                await check_units_exist_and_belong_store(check_ids=unit_ids, store_id=dto.store_id)
                action_id = await self.db.actions_transactions.new_price(user_id=user_id, data=dto)

            case ActionEnum.stockReturn:
                check_role_in_store(roles_can_stock_return)
                units = await check_units_exist_and_belong_store(
                    check_ids=unit_ids, store_id=dto.store_id
                )
                stock_return_transactions: list[StockReturnTransaction] = cast(
                    list[StockReturnTransaction], dto.transactions
                )
                check_quantity_positive(
                    check_units=units, transactions=tuple(stock_return_transactions)
                )
                action_id = await self.db.actions_transactions.stock_return(
                    user_id=user_id, data=dto
                )
            case _:
                raise ValueError(f"Unknown action: {dto.action}")

        await self.db.commit()
        return action_id

    async def get_actions(
        self,
        offset: int,
        limit: int,
        search_term: ActionFilter,
        user_id: int,
        store_id: int | None,
        user_role_in_company: RoleUserInCompanyEnum,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
    ) -> tuple[list[ActionWithUnitsTransactionsDTO], Pagination]:
        """
        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        :raise StoreAccessForbiddenException: Если нет прав чтения действий в store.
        :raise ActionNotFoundException: Если не найдено ни одного `действия` с учетом пагинации и фильтров.
        """
        # todo популярный ендпоинт желательно в один запрос или использовать кэш для проверок
        if user_role_in_company in roles_is_administrations:
            # Админ — можно всё, только проверяем, если store_id указан, что магазин существует
            if store_id:
                await StoresService(db=self.db, cache=self.cache).check_get_store_by_id(
                    store_id=store_id
                )
        else:
            # Не админ — store_id обязателен
            if not store_id:
                raise AllStoresAccessForbiddenException
            else:
                await StoresService(db=self.db, cache=self.cache).check_get_store_by_id(
                    store_id=store_id
                )
                if user_roles_in_stores.get(store_id) not in roles_can_read_action_in_store:
                    raise StoreAccessForbiddenException

        actions_with_units = await self.db.actions.get_actions_with_units(
            offset=offset,
            limit=limit,
            search_term=search_term,
            store_id=store_id,
        )
        if not actions_with_units:
            raise ActionNotFoundException

        total = await self.db.actions.get_total()
        pagination = Pagination(offset=offset, limit=limit, total=total)
        return actions_with_units, pagination

    async def get_action(
        self,
        action_id: int,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        user_role_in_company: RoleUserInCompanyEnum,
    ) -> ActionWithTransactionsDTO:
        """
        :raise ActionNotFoundException: если action не найден
        :raise StoreAccessForbiddenException: Если нет прав чтения действий в store.
        """
        action = await self.check_get_action_by_id(action_id=action_id)
        if user_role_in_company not in roles_is_administrations:
            if user_roles_in_stores.get(action.store_id) not in roles_can_read_action_in_store:
                raise StoreAccessForbiddenException

        transactions = await self.db.actions_transactions.get_transactions_with_units(
            action_id=action_id
        )

        return ActionWithTransactionsDTO(**action.model_dump(), transactions=transactions)

    @cache_service_method_by_id(return_type=ActionDTO, ttl=60 * 60 * 24)
    async def check_get_action_by_id(self, action_id: int) -> ActionDTO:
        """
        Cached method: 24 hours
        :raise ActionNotFoundException: если action не найден
        """
        try:
            action = await self.db.actions.get_one(id=action_id)
        except ObjectNotFoundException as exc:
            raise ActionNotFoundException from exc
        return action
