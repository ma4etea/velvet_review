from collections import defaultdict
from typing import Any

from sqlalchemy import (
    select,
    literal,
    insert,
    union_all,
    update,
    cast,
    Float,
    CTE,
    join,
    ColumnElement,
    Select,
)
from sqlalchemy.orm import joinedload

from src.logging_config import logger
from src.models.actions import ActionTransactionOrm, ActionOrm, ActionEnum
from src.models.units import UnitORM, StoreORM
from src.repositories.db.base import BaseRepository
from src.repositories.db.mappers.mappers import (
    ActionsDataMapper,
    ActionsTransactionsDataMapper,
    ActionWithUnitsTransactionsDataMapper,
    ActionsTransactionsWithUnitDataMapper,
)
from src.schemas.actions import (
    ActionIdDTO,
    AddActionDTO,
    ActionWithUnitsTransactionsDTO,
    ActionDTO,
    ActionTransactionDTO,
    SalesTransaction,
    ActionTransactionWithUnitDTO,
)
from src.utils.sql import sql_debag


class ActionsRepository(BaseRepository[ActionOrm, ActionDTO]):
    model = ActionOrm
    mapper = ActionsDataMapper

    async def get_actions_with_units(
        self, store_id: int | None, offset: int, limit: int, search_term: str | None
    ) -> list[ActionWithUnitsTransactionsDTO]:
        """
        Почему не простым способом?
        Потому что бы хочется вытянуть только определенные поля, что бы снизить нагрузку.
        """
        # получаем actions
        filters: list[ColumnElement[bool]] = []
        if search_term:
            filters.append(self.model.title == search_term)
        if store_id:
            filters.append(self.model.store_id == store_id)
        actions_query = (
            select(
                self.model.id,
                self.model.title,
                self.model.created_at,
                self.model.store_id,
                StoreORM.title.label("store_title"),
            )
            .select_from(
                join(left=self.model, right=StoreORM, onclause=self.model.store_id == StoreORM.id)
            )
            .filter(*filters)
            .offset(offset)
            .limit(limit)
        )
        actions_result = await self.session.execute(actions_query)
        actions_map: defaultdict[int, Any] = defaultdict(dict)
        actions_ids: list[int] = list()
        for row in actions_result.mappings().all():  # создаем map по ключам action_id
            action_dict = dict(row)
            action_dict["transactions"] = []
            actions_map[action_dict["id"]] = action_dict
            actions_ids.append(action_dict["id"])  # собираем id для запроса transactions_query

        # получаем транзакции с именами товара
        transactions_query = (
            select(
                ActionTransactionOrm.id.label("transaction_id"),
                ActionTransactionOrm.action_id,
                UnitORM.id.label("unit_id"),
                UnitORM.title,
            )
            .select_from(
                join(
                    left=ActionTransactionOrm,
                    right=UnitORM,
                    onclause=ActionTransactionOrm.unit_id == UnitORM.id,
                )
            )
            .filter(ActionTransactionOrm.action_id.in_(actions_ids))
        )
        transactions_result = await self.session.execute(transactions_query)
        for row in transactions_result.mappings().all():  # расфасовываем транзакции в map по ключам
            transaction_dict = dict(row)
            actions_map[transaction_dict["action_id"]]["transactions"].append(transaction_dict)

        return [
            ActionWithUnitsTransactionsDataMapper.to_domain(action)
            for action in actions_map.values()
        ]


class ActionsTransactionsRepository(BaseRepository[ActionTransactionOrm, ActionTransactionDTO]):
    model = ActionTransactionOrm
    mapper = ActionsTransactionsDataMapper

    async def add_stock(self, user_id: int, data: AddActionDTO) -> ActionIdDTO:
        """
        1. Выполнить unit_ops_cte → сформировать виртуальную таблицу из data, согласно логики действия(addStock)
        2. Выполнить updated_unit_cte → обновить товары, согласно логики действия(addStock) и вернуть новые значения
        3. Выполнить add_action_cte → вставить в таблицу новую запись действия(addStock)
        4. Выполнить SELECT с JOIN → собрать все данные, согласно логики действия(addStock), для вставки в actions_transactions
        """
        # Создаем поля для виртуальной таблицы unit_ops_cte
        ops_values: list[Select[tuple[int, float | None, float | None, float | None, int]]] = [
            select(
                literal(transaction.unit_id).label("unit_id"),
                literal(getattr(transaction, "quantity_delta", None)).label("quantity_delta"),
                literal(getattr(transaction, "cost_price", None)).label("cost_price"),
                literal(getattr(transaction, "retail_price", None)).label("retail_price"),
                literal(i).label(
                    "row_num"
                ),  # поле для order_by, что бы сохранился порядок от пользователя
            )
            for i, transaction in enumerate(data.transactions)
        ]

        unit_ops_cte = union_all(*ops_values).cte("unit_ops")

        # обновляем поля, используем математические вычисления
        updated_unit_values = dict(
            quantity=UnitORM.quantity
            + unit_ops_cte.c.quantity_delta,  # Добавляет к запасу количество товара.
            # Высчитывает новую закупочную среднюю цену.
            average_cost_price=(
                UnitORM.average_cost_price * UnitORM.quantity
                + unit_ops_cte.c.cost_price * unit_ops_cte.c.quantity_delta
            )
            / cast((UnitORM.quantity + unit_ops_cte.c.quantity_delta), Float),
            # Устанавливает новую продажную цену.
            retail_price=unit_ops_cte.c.retail_price,
        )
        edit_unit_cte = self._updated_unit_cte(
            UnitORM.id == unit_ops_cte.c.unit_id, **updated_unit_values
        )

        # создаем action, нужен его id в дальнейшем
        add_action_cte = self._insert_action_cte(title=data.action, store_id=data.store_id)

        # Значения полей которые вставляем в таблицу actions_transactions
        select_values_map = self._create_select_values(
            quantity_delta=unit_ops_cte.c.quantity_delta,  # Какое количество товара прибавилось на момент поступления
            cost_price=unit_ops_cte.c.cost_price,  # Закупочная цена в это поступлении
            retail_price=unit_ops_cte.c.retail_price,  # Продажная цена на момент поступления
            previous_retail_price=edit_unit_cte.c.previous_retail_price,  # Пред идущая цена
            discount_price=None,  # Реальная цена продажи
            action=add_action_cte.c.title,
            unit_id=edit_unit_cte.c.id,
            user_id=user_id,
            action_id=add_action_cte.c.id,
            store_id=edit_unit_cte.c.store_id,
        )

        return await self._add_action_transactions(
            unit_ops_cte, edit_unit_cte, add_action_cte, select_values_map
        )

    async def sales(
        self,
        user_id: int,
        store_id: int,
        action: ActionEnum,
        sales_transactions: list[SalesTransaction],
    ) -> ActionIdDTO:
        """
        1. Выполнить unit_ops_cte → сформировать виртуальную таблицу из data, согласно логики действия(sales)
        2. Выполнить updated_unit_cte → обновить товары, согласно логики действия(sales) и вернуть новые значения
        3. Выполнить add_action_cte → вставить в таблицу новую запись действия(sales)
        4. Выполнить SELECT с JOIN → собрать все данные, согласно логики действия(sales), для вставки в actions_transactions

        Raises:
            Exception
        """
        # Создаем поля для виртуальной таблицы unit_ops_cte
        ops_values = [
            select(
                literal(transaction.unit_id).label("unit_id"),
                literal(transaction.quantity_delta).label("quantity_delta"),
                literal(transaction.discount_price).label("discount_price"),
                literal(i).label(
                    "row_num"
                ),  # поле для order_by, что бы сохранился порядок от пользователя
            )
            for i, transaction in enumerate(sales_transactions)
        ]

        unit_ops_cte = union_all(*ops_values).cte("unit_ops")

        # обновляем поля, используем математические вычисления
        updated_unit_values = dict(
            quantity=UnitORM.quantity
            - unit_ops_cte.c.quantity_delta,  # отнимает количество товара при продаже
        )
        edit_unit_cte = self._updated_unit_cte(
            UnitORM.id == unit_ops_cte.c.unit_id, **updated_unit_values
        )

        # создаем action, нужен его id в дальнейшем
        add_action_cte = self._insert_action_cte(title=action, store_id=store_id)

        # Значения полей которые вставляем в таблицу actions_transactions
        select_values_map = self._create_select_values(
            quantity_delta=unit_ops_cte.c.quantity_delta,  # сколько товара продалось
            # Закупочную цену берем из товара, что бы высчитать прибыль на момент транзакции
            cost_price=edit_unit_cte.c.average_cost_price,
            # Цену продажи берем из товара, что бы можно было высчитать скидку на момент транзакции
            retail_price=edit_unit_cte.c.retail_price,
            previous_retail_price=None,
            discount_price=unit_ops_cte.c.discount_price,  # Реальная цена продажи
            action=add_action_cte.c.title,
            unit_id=edit_unit_cte.c.id,
            user_id=user_id,
            action_id=add_action_cte.c.id,
            store_id=edit_unit_cte.c.store_id,
        )

        return await self._add_action_transactions(
            unit_ops_cte, edit_unit_cte, add_action_cte, select_values_map
        )

    async def sales_return(self, user_id: int, data: AddActionDTO) -> ActionIdDTO:
        """
        1. Выполнить unit_ops_cte → сформировать виртуальную таблицу из data, согласно логики действия(sales_return)
        2. Выполнить updated_unit_cte → обновить товары, согласно логики действия(sales_return) и вернуть новые значения
        3. Выполнить add_action_cte → вставить в таблицу новую запись действия(sales_return)
        4. Выполнить SELECT с JOIN → собрать все данные, согласно логики действия(sales_return), для вставки в actions_transactions

        Raises:
            Exception
        """
        # Создаем поля для виртуальной таблицы unit_ops_cte
        ops_values: list[Select[tuple[int, float | None, float | None, int]]] = [
            select(
                literal(transaction.unit_id).label("unit_id"),
                literal(getattr(transaction, "quantity_delta", None)).label("quantity_delta"),
                literal(getattr(transaction, "discount_price", None)).label("discount_price"),
                literal(i).label(
                    "row_num"
                ),  # поле для order_by, что бы сохранился порядок от пользователя
            )
            for i, transaction in enumerate(data.transactions)
        ]

        unit_ops_cte = union_all(*ops_values).cte("unit_ops")

        # обновляем поля, используем математические вычисления
        updated_unit_values = dict(
            quantity=UnitORM.quantity + unit_ops_cte.c.quantity_delta,
            # Прибавлять количество товара при возврате отвара
        )
        edit_unit_cte = self._updated_unit_cte(
            UnitORM.id == unit_ops_cte.c.unit_id, **updated_unit_values
        )

        # создаем action, нужен его id в дальнейшем
        add_action_cte = self._insert_action_cte(title=data.action, store_id=data.store_id)

        # Значения полей которые вставляем в таблицу actions_transactions
        select_values_map = self._create_select_values(
            quantity_delta=unit_ops_cte.c.quantity_delta,  # сколько товара вернулось от покупателя
            # Закупочную цену берем из товара, что бы высчитать потерянную прибыль на момент транзакции
            cost_price=edit_unit_cte.c.average_cost_price,
            # Цену продажи берем из товара, что бы можно было высчитать какая была скидка на момент транзакции
            retail_price=edit_unit_cte.c.retail_price,
            # todo возможно: цена возврата не должна превышать цену продажи или цену.
            #  А может возврат делать только на конкретную продажу
            previous_retail_price=None,
            discount_price=unit_ops_cte.c.discount_price,  # Реальная цена продажи для возврата
            action=add_action_cte.c.title,
            unit_id=edit_unit_cte.c.id,
            user_id=user_id,
            action_id=add_action_cte.c.id,
            store_id=edit_unit_cte.c.store_id,
        )

        return await self._add_action_transactions(
            unit_ops_cte, edit_unit_cte, add_action_cte, select_values_map
        )

    async def write_off(self, user_id: int, data: AddActionDTO) -> ActionIdDTO:
        """
        1. Выполнить unit_ops_cte → сформировать виртуальную таблицу из data, согласно логики действия(write_off)
        2. Выполнить updated_unit_cte → обновить товары, согласно логики действия(write_off) и вернуть новые значения
        3. Выполнить add_action_cte → вставить в таблицу новую запись действия(write_off)
        4. Выполнить SELECT с JOIN → собрать все данные, согласно логики действия(write_off), для вставки в actions_transactions

        Raises:
            Exception
        """
        # Создаем поля для виртуальной таблицы unit_ops_cte
        ops_values: list[Select[tuple[int, float | None, int]]] = [
            select(
                literal(transaction.unit_id).label("unit_id"),
                literal(getattr(transaction, "quantity_delta", None)).label("quantity_delta"),
                literal(i).label(
                    "row_num"
                ),  # поле для order_by, что бы сохранился порядок от пользователя
            )
            for i, transaction in enumerate(data.transactions)
        ]
        unit_ops_cte = union_all(*ops_values).cte("unit_ops")

        # обновляем поля, используем математические вычисления
        updated_unit_values = dict(
            quantity=UnitORM.quantity
            - unit_ops_cte.c.quantity_delta,  # отнимает количество товара.
        )
        edit_unit_cte = self._updated_unit_cte(
            UnitORM.id == unit_ops_cte.c.unit_id, **updated_unit_values
        )

        # создаем action, нужен его id в дальнейшем
        add_action_cte = self._insert_action_cte(title=data.action, store_id=data.store_id)

        # Значения полей которые вставляем в таблицу actions_transactions
        select_values_map = self._create_select_values(
            quantity_delta=unit_ops_cte.c.quantity_delta,  # Какое количество товара отнимается на момент списания
            cost_price=edit_unit_cte.c.average_cost_price,  # Закупочная цена на момент списания
            retail_price=edit_unit_cte.c.retail_price,  # Продажная цена на момент списания
            previous_retail_price=None,
            discount_price=None,
            action=add_action_cte.c.title,
            unit_id=edit_unit_cte.c.id,
            user_id=user_id,
            action_id=add_action_cte.c.id,
            store_id=edit_unit_cte.c.store_id,
        )

        return await self._add_action_transactions(
            unit_ops_cte, edit_unit_cte, add_action_cte, select_values_map
        )

    async def new_price(self, user_id: int, data: AddActionDTO) -> ActionIdDTO:
        """
        1. Выполнить unit_ops_cte → сформировать виртуальную таблицу из data, согласно логики действия(new_price)
        2. Выполнить updated_unit_cte → обновить товары, согласно логики действия(new_price) и вернуть новые значения
        3. Выполнить add_action_cte → вставить в таблицу новую запись действия(new_price)
        4. Выполнить SELECT с JOIN → собрать все данные, согласно логики действия(new_price), для вставки в actions_transactions

        Raises:
            Exception
        """
        # Создаем поля для виртуальной таблицы unit_ops_cte
        ops_values: list[Select[tuple[int, float | None, int]]] = [
            select(
                literal(transaction.unit_id).label("unit_id"),
                literal(getattr(transaction, "retail_price", None)).label("retail_price"),
                literal(i).label("row_num"),
            )
            for i, transaction in enumerate(data.transactions)
        ]
        unit_ops_cte = union_all(*ops_values).cte("unit_ops")

        # запрос к unit до изменения
        unit_cte = (
            select(UnitORM.retail_price)
            .select_from(UnitORM)
            .filter(UnitORM.id == unit_ops_cte.c.unit_id)
        )

        # обновляем поля, используем математические вычисления
        updated_unit_values = dict(
            retail_price=unit_ops_cte.c.retail_price,  # Выставляет новую цену
        )
        edit_unit_cte = self._updated_unit_cte(
            UnitORM.id == unit_ops_cte.c.unit_id, **updated_unit_values
        )

        # создаем action, нужен его id в дальнейшем
        add_action_cte = self._insert_action_cte(title=data.action, store_id=data.store_id)

        # Значения полей которые вставляем в таблицу actions_transactions
        select_values_map = self._create_select_values(
            quantity_delta=None,
            cost_price=None,
            retail_price=unit_ops_cte.c.retail_price,  # новая цена
            previous_retail_price=unit_cte.c.retail_price,  # Пред идущая цена
            discount_price=None,
            action=add_action_cte.c.title,
            unit_id=edit_unit_cte.c.id,
            user_id=user_id,
            action_id=add_action_cte.c.id,
            store_id=edit_unit_cte.c.store_id,
        )

        return await self._add_action_transactions(
            unit_ops_cte, edit_unit_cte, add_action_cte, select_values_map
        )

    async def stock_return(self, user_id: int, data: AddActionDTO) -> ActionIdDTO:
        """
        1. Выполнить unit_ops_cte → сформировать виртуальную таблицу из data, согласно логики действия(stock_return)
        2. Выполнить updated_unit_cte → обновить товары, согласно логики действия(stock_return) и вернуть новые значения
        3. Выполнить add_action_cte → вставить в таблицу новую запись действия(stock_return)
        4. Выполнить SELECT с JOIN → собрать все данные, согласно логики действия(stock_return), для вставки в actions_transactions

        Raises:
            Exception
        """
        # Создаем поля для виртуальной таблицы unit_ops_cte
        ops_values: list[Select[tuple[int, float | None, float | None, int]]] = [
            select(
                literal(transaction.unit_id).label("unit_id"),
                literal(getattr(transaction, "quantity_delta", None)).label("quantity_delta"),
                literal(getattr(transaction, "cost_price", None)).label("cost_price"),
                literal(i).label("row_num"),
            )
            for i, transaction in enumerate(data.transactions)
        ]

        unit_ops_cte = union_all(*ops_values).cte("unit_ops")

        # обновляем поля, используем математические вычисления
        updated_unit_values = dict(
            quantity=UnitORM.quantity
            - unit_ops_cte.c.quantity_delta,  # Отнимаем из запаса количество товара.
        )
        edit_unit_cte = self._updated_unit_cte(
            UnitORM.id == unit_ops_cte.c.unit_id, **updated_unit_values
        )

        # создаем action, нужен его id в дальнейшем
        add_action_cte = self._insert_action_cte(data.action, data.store_id)

        # Значения полей которые вставляем в таблицу actions_transactions
        select_values_map = self._create_select_values(
            quantity_delta=unit_ops_cte.c.quantity_delta,
            # Какое количество товара отнялось на момент возврата поставщику
            cost_price=unit_ops_cte.c.cost_price,  # Закупочная цена на момент поступления возврата поставщику
            retail_price=None,
            previous_retail_price=None,
            discount_price=None,
            action=add_action_cte.c.title,
            unit_id=edit_unit_cte.c.id,
            user_id=user_id,
            action_id=add_action_cte.c.id,
            store_id=edit_unit_cte.c.store_id,
        )

        return await self._add_action_transactions(
            unit_ops_cte, edit_unit_cte, add_action_cte, select_values_map
        )

    def _create_select_values(
        self,
        quantity_delta: Any,
        cost_price: Any,
        retail_price: Any,
        previous_retail_price: Any,
        discount_price: Any,
        action: Any,
        unit_id: Any,
        user_id: Any,
        action_id: Any,
        store_id: Any,
    ) -> dict[str, Any]:
        """
        Поля таблицы actions_transactions:
        - quantity_delta: Изменение количества товара (положительное при поступлении, отрицательное при продаже).
        - cost_price: Себестоимость товара на момент транзакции.
        - retail_price: Розничная цена товара на момент транзакции.
        - previous_retail_price: Пред идущая продажная цена.
        - discount_price: Скидочная цена, применённая к товару при транзакции.
        - action: Тип действия (например, 'sales', 'addStock' и т.д.).
        - unit_id: ID товара (единицы), на который влияет транзакция.
        - user_id: ID пользователя, совершившего действие.
        - action_id: ID соответствующей записи в таблице actions.
        - store_id: ID магазина, в котором произошла транзакция.
        """
        # locals() возвращает словарь аргументов в порядке определения
        args = locals()
        args.pop("self")  # убираем self
        return args

    async def _add_action_transactions(
        self,
        unit_ops_cte: CTE,
        edit_unit_cte: CTE,
        add_action_cte: CTE,
        select_values_map: dict[str, Any],
    ) -> ActionIdDTO:
        insert_columns = list(select_values_map.keys())

        select_values = [select_values_map[column] for column in insert_columns]

        action_transactions_query = (
            select(*select_values)
            .select_from(
                edit_unit_cte.join(unit_ops_cte, edit_unit_cte.c.id == unit_ops_cte.c.unit_id).join(
                    add_action_cte, literal(True)
                )
            )
            .order_by(unit_ops_cte.c.row_num)
        )

        add_action_transactions = (
            insert(self.model)
            .from_select(names=insert_columns, select=action_transactions_query)
            .cte("add_action_transactions")
        )

        create_action = (
            select(add_action_cte.c.id, add_action_cte.c.title).add_cte(
                add_action_transactions
            )  # регистрируем зависимость
        )
        logger.debug(sql_debag(create_action))
        try:
            result = await self.session.execute(create_action)
            action_id = result.scalar_one()
            return ActionIdDTO(id=action_id)
        except:
            raise

    def _insert_action_cte(self, title: ActionEnum, store_id: int) -> CTE:
        """
        Добавляет action в базу
        """
        return (
            insert(ActionOrm)
            .values(title=title, store_id=store_id)
            .returning(ActionOrm.id, ActionOrm.title)
            .cte("add_action")
        )

    def _updated_unit_cte(self, *filter_: ColumnElement[Any], **values: ColumnElement[Any]) -> CTE:
        """
        Обновляет переданные поля у товара
        """
        # Снимок состояния юнитов до апдейта
        before_update_unit_cte = (
            select(UnitORM.id, UnitORM.retail_price)
            .select_from(UnitORM)
            .filter(*filter_)
            .cte("before_update_unit_cte")
        )

        return (
            update(UnitORM)
            .add_cte(before_update_unit_cte)
            .values(**values)
            .filter(*filter_)
            .returning(
                UnitORM.id,
                UnitORM.quantity,
                UnitORM.average_cost_price,
                UnitORM.retail_price,
                (
                    select(before_update_unit_cte.c.retail_price)
                    .select_from(before_update_unit_cte)
                    .filter(before_update_unit_cte.c.id == UnitORM.id)
                    .label("previous_retail_price")
                ),
                UnitORM.store_id,
            )
            .cte("updated_unit")
        )

    async def get_transactions_with_units(
        self, action_id: int
    ) -> list[ActionTransactionWithUnitDTO]:
        """
        Получает все транзакции со связанными товарами.
        """
        query = (
            select(self.model)
            .select_from(self.model)
            .filter_by(action_id=action_id)
            .options(joinedload(self.model.unit).joinedload(UnitORM.main_image))
        )

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [ActionsTransactionsWithUnitDataMapper.to_domain(model) for model in models]
