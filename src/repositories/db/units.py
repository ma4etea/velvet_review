from sqlalchemy import select, func, or_, desc, ColumnElement
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import selectinload, joinedload

from src.exceptions.base import ObjectNotUniqueException
from src.exceptions.not_found import ObjectNotFoundException
from src.models.units import UnitORM
from src.repositories.db.base import BaseRepository
from src.repositories.db.mappers.mappers import (
    UnitsDataMapper,
    UnitWithActionsDataMapper,
    UnitWithMainImageDataMapper,
)
from src.schemas.types import SortUnitBy, SortOrder, UnitField
from src.schemas.units import UnitDTO, UnitWithFieldsDTO, EditUnitDTO, UnitWithMainImageDTO


class UnitsRepository(BaseRepository[UnitORM, UnitDTO]):
    model = UnitORM
    mapper = UnitsDataMapper

    async def get_units(
        self,
        offset: int,
        limit: int,
        search_term: str | None = None,
        store_id: int | None = None,
        sort_order: SortOrder = SortOrder.desc,
        sort_unit_by: SortUnitBy = SortUnitBy.id,
    ) -> list[UnitWithMainImageDTO]:
        """
        получить список товаров, отфильтровать по search_term и store_id
        """
        filters: list[ColumnElement[bool]] = []

        if search_term:
            st = search_term.strip().lower()
            filters.append(
                or_(
                    func.lower(self.model.title).contains(st),
                    func.lower(self.model.description).contains(st),
                )
            )

        if store_id:
            filters.append(self.model.store_id == store_id)

        query = (
            select(self.model)
            .select_from(self.model)
            .filter(*filters)
            .offset(offset)
            .limit(limit)
            .options(joinedload(self.model.main_image))
        )

        order_column = getattr(self.model, sort_unit_by)
        query = query.order_by(desc(order_column) if sort_order == SortOrder.desc else order_column)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [UnitWithMainImageDataMapper.to_domain(model) for model in models]

    async def get_unit_with_fields(
        self, unit_id: int, fields: tuple[UnitField, ...] | None = None
    ) -> UnitWithFieldsDTO:
        """
        :raise ObjectNotFoundException: Если ни одного не найдено.
        :raise ObjectNotUniqueException: Если больше одного найдено
        """
        query = select(self.model).filter_by(id=unit_id)
        if fields is not None:
            if UnitField.transactions in fields:
                query = query.options(selectinload(self.model.transactions))
            if UnitField.images in fields:
                query = query.options(selectinload(self.model.images))
            if UnitField.main_image in fields:
                query = query.options(joinedload(self.model.main_image))

        try:
            result = await self.session.execute(query)
            model = result.scalar_one()
            return UnitWithActionsDataMapper.to_domain(model, exclude_lazy=True)
        except NoResultFound as exc:
            raise ObjectNotFoundException from exc
        except MultipleResultsFound as exc:
            raise ObjectNotUniqueException from exc

    async def edit_unit(self, unit_id: int, dto: EditUnitDTO) -> UnitDTO:
        return await self.edit(dto=dto, exclude_unset=True, id=unit_id)
