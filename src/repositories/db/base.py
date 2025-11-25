from typing import Generic, Any

from asyncpg import (  # type: ignore reportMissingTypeStubs
    UniqueViolationError,
    ForeignKeyViolationError,
)
from sqlalchemy.exc import IntegrityError, NoResultFound, MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Insert, delete, update, func, ColumnElement

from src.exceptions.base import (
    ObjectAlreadyExistsException,
    ObjectUseAsForeignKeyException,
    ObjectNotUniqueException,
)
from src.exceptions.not_found import ObjectNotFoundException, ForeignKeyNotFoundException

from src.repositories.db.mappers.base import DataMapper, ModelType, SchemaType
from src.schemas.base import BaseSchema
from src.utils.exceptions import is_raise


class BaseRepository(Generic[ModelType, SchemaType]):
    model: type[ModelType]
    mapper: type[DataMapper[ModelType, SchemaType]]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_by_ids(self, *ids: int, **filter_by: Any) -> list[SchemaType]:
        filter_ = self.model.id.in_(ids)
        return await self.get_all(filter_, **filter_by)

    async def get_all(
        self,
        *filter_: ColumnElement[Any],
        offset: int | None = None,
        limit: int | None = None,
        **filter_by: Any,
    ) -> list[SchemaType]:
        query = select(self.model).filter(*filter_).filter_by(**filter_by)
        if offset:
            query = query.offset(offset=offset)
        if limit:
            query = query.limit(limit=limit)

        try:
            result = await self.session.execute(query)
            models = result.scalars().all()
            res = [self.mapper.to_domain(model) for model in models]
            return res

        except:
            raise

    async def get_one_or_none(
        self, *filter_: ColumnElement[Any], **filter_by: Any
    ) -> SchemaType | None:
        """
        :raise ObjectNotUniqueException: Если больше одного найдено
        """
        try:
            query = select(self.model).filter(*filter_).filter_by(**filter_by)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            if model is not None:
                return self.mapper.to_domain(model)
            return None

        except MultipleResultsFound as exc:
            raise ObjectNotUniqueException from exc

    async def get_one(self, *filter_: ColumnElement[Any], **filter_by: Any) -> SchemaType:
        """
        :raise ObjectNotFoundException: Если ни одного не найдено.
        :raise ObjectNotUniqueException: Если больше одного найдено
        """
        query = select(self.model).filter(*filter_).filter_by(**filter_by)
        try:
            result = await self.session.execute(query)
            model = result.scalar_one()
            return self.mapper.to_domain(model)

        except NoResultFound as exc:
            raise ObjectNotFoundException from exc
        except MultipleResultsFound as exc:
            raise ObjectNotUniqueException from exc

    async def add(self, dto: BaseSchema):
        """
        :raise ObjectAlreadyExistsException: Если объект обязан быть уникальными и он уже существует.
        :raise ForeignKeyNotFoundException: Если не найден внешний ключ при создании строки.
        :raise ObjectNotFoundException: Если ни одного не найдено.
        :raise ObjectNotUniqueException: Если больше одного найдено
        """
        stmt = Insert(self.model).values(**dto.model_dump()).returning(self.model)
        try:
            result = await self.session.execute(stmt)
            model = result.scalar_one()
            return self.mapper.to_domain(model)
        except NoResultFound as exc:
            raise ObjectNotFoundException from exc
        except MultipleResultsFound as exc:
            raise ObjectNotUniqueException from exc
        except IntegrityError as exc:
            is_raise(exc, UniqueViolationError, ObjectAlreadyExistsException)
            is_raise(exc, ForeignKeyViolationError, ForeignKeyNotFoundException)
            raise exc

    async def add_bulk(self, *dtos: BaseSchema):
        stmt = Insert(self.model).values([dto.model_dump() for dto in dtos]).returning(self.model)
        try:
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [self.mapper.to_domain(model) for model in models]
        except:
            raise

    async def edit(
        self,
        dto: BaseSchema,
        *filter_: ColumnElement[Any],
        exclude_unset: bool = False,
        **filter_by: Any,
    ) -> SchemaType:
        """
        :raise ForeignKeyNotFoundException: Если не найден внешний ключ при создании строки.
        :raise ObjectNotFoundException: Если ни одного не найдено.
        :raise ObjectNotUniqueException: Если больше одного найдено
        """
        stmt = (
            update(self.model)
            .filter(*filter_)
            .filter_by(**filter_by)
            .values(**dto.model_dump(exclude_unset=exclude_unset))
        ).returning(self.model)
        try:
            result = await self.session.execute(stmt)
            model = result.scalar_one()
            return self.mapper.to_domain(model)
        except IntegrityError as exc:
            is_raise(exc, ForeignKeyViolationError, ForeignKeyNotFoundException)
            raise exc
        except NoResultFound as exc:
            raise ObjectNotFoundException from exc
        except MultipleResultsFound as exc:
            raise ObjectNotUniqueException from exc

    async def delete(self, **filter_by: Any):
        """
        :raise ObjectNotFoundException: Если ни одного не найдено.
        :raise ObjectNotUniqueException: Если больше одного найдено
        :raise ObjectUseAsForeignKeyException: Если при удалении ключ объекта используется как ForeignKey.
        """
        await self.get_one(**filter_by)

        try:
            stmt = delete(self.model).filter_by(**filter_by)
            await self.session.execute(stmt)
        except IntegrityError as exc:
            is_raise(exc, ForeignKeyViolationError, ObjectUseAsForeignKeyException)
            raise exc

    async def delete_bulk(self, *filter_: ColumnElement[Any], **filter_by: Any):
        stmt = delete(self.model).filter(*filter_).filter_by(**filter_by)
        await self.session.execute(stmt)

    async def get_total(self, *filter_: ColumnElement[Any], **filter_by: Any) -> int:
        """
        :return: Общее количество объектов
        """
        query = (
            select(func.count("*")).select_from(self.model).filter(*filter_).filter_by(**filter_by)
        )
        res = await self.session.execute(query)
        total: int = res.scalar_one()
        return total

    # async def _safe_execute_one(self, stmt: Executable) -> BaseModel:
    #     try:
    #         result = await self.session.execute(stmt)
    #         model = result.scalar_one()
    #         return model
    #     except NoResultFound:
    #         raise ObjectNotFoundException
    #     except DBAPIError as exc:
    #         logger.warning("Поймана ошибка в: DBAPIError")
    #         is_raise(exc=exc, reason=DataError, to_raise=TypeErrorException,
    #                  check_message_contains="object cannot be interpreted as an integer")
    #         # is_raise(exc=exc, reason=DataError, to_raise=ToBigIdException)
    #
    #         is_raise(exc=exc, reason=PostgresSyntaxError, to_raise=StmtSyntaxErrorException)
    #         # is_raise(exc=exc, reason=NotNullViolationError, to_raise=NotNullViolationException)
    #         logger.error(exc_log_string(exc))
    #         raise exc
    #     except Exception as exc:
    #         logger.error(exc_log_string(exc))
    #         raise exc
    #
    # async def _safe_execute_all(self, stmt: Executable) -> Result:
    #     try:
    #         result = await self.session.execute(stmt)
    #         return result
    #     except NoResultFound:
    #         raise ObjectNotFoundException
    #     except DBAPIError as exc:
    #         # is_raise(
    #         #     exc,
    #         #     DataError,
    #         #     OffsetToBigException,
    #         #     check_message_contains=("value out of int64 range", "LIMIT", "OFFSET"),
    #         # )
    #         # is_raise(
    #         #     exc,
    #         #     DataError,
    #         #     LimitToBigException,
    #         #     check_message_contains=("value out of int64 range", "LIMIT"),
    #         # )
    #         # is_raise(
    #         #     exc,
    #         #     DataError,
    #         #     ToBigIdException,
    #         #     check_message_contains=("value out of int32 range",),
    #         # )
    #         raise exc
    #     except Exception as exc:
    #         logger.error(exc_log_string(exc))
    #         raise exc

    # def build_dict_fields(self, **kwargs) -> dict:
    #     return kwargs
