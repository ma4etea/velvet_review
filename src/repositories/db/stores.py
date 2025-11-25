from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import selectinload, joinedload

from src.exceptions.base import ObjectNotUniqueException
from src.exceptions.not_found import ObjectNotFoundException
from src.models.units import StoreORM
from src.models.users import RoleUserInStoreORM
from src.repositories.db.base import BaseRepository
from src.repositories.db.mappers.mappers import (
    StoresDataMapper,
    RoleUserInStoreDataMapper,
    StoreWithUsersMapper,
)
from src.schemas.stores import StoreWithRoleUsersDTO, StoreDTO, RoleUserInStoreDTO


class StoresRepository(BaseRepository[StoreORM, StoreDTO]):
    model = StoreORM
    mapper = StoresDataMapper

    async def get_store_with_users(self, store_id: int) -> StoreWithRoleUsersDTO:
        """
        :raise ObjectNotFoundException: Если ни одного не найдено.
        :raise ObjectNotUniqueException: Если больше одного найдено
        """
        query = (
            select(self.model)
            .filter_by(id=store_id)
            .options(selectinload(self.model.roles).options(joinedload(RoleUserInStoreORM.user)))
        )
        try:
            result = await self.session.execute(query)
            model = result.scalar_one()
            return StoreWithUsersMapper.to_domain(model)
        except NoResultFound as exc:
            raise ObjectNotFoundException from exc
        except MultipleResultsFound as exc:
            raise ObjectNotUniqueException from exc


class RoleUserInStoreRepository(BaseRepository[RoleUserInStoreORM, RoleUserInStoreDTO]):
    model = RoleUserInStoreORM
    mapper = RoleUserInStoreDataMapper
