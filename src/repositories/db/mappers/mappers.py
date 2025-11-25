from src.models.actions import ActionTransactionOrm, ActionOrm
from src.models.notifications import NotificationORM
from src.models.units import UnitORM, StoreORM, UnitImageORM
from src.models.users import UserORM, SessionORM, RoleUserInStoreORM
from src.repositories.db.mappers.base import DataMapper
from src.schemas.actions import (
    ActionTransactionDTO,
    ActionWithUnitsTransactionsDTO,
    ActionDTO,
    ActionTransactionWithUnitDTO,
)
from src.schemas.stores import StoreDTO, RoleUserInStoreDTO, StoreWithRoleUsersDTO
from src.schemas.units import UnitDTO, UnitWithFieldsDTO, UnitWithMainImageDTO
from src.schemas.unit_images import UnitImageDTO
from src.schemas.users import UserDTO
from src.schemas.notifications import NotificationDTO
from src.schemas.auths import UserSessionDTO


class UsersDataMapper(DataMapper[UserORM, UserDTO]):
    model = UserORM
    schema = UserDTO


class StoreWithUsersMapper(DataMapper[StoreORM, StoreWithRoleUsersDTO]):
    model = StoreORM
    schema = StoreWithRoleUsersDTO


class StoresDataMapper(DataMapper[StoreORM, StoreDTO]):
    model = StoreORM
    schema = StoreDTO


class RoleUserInStoreDataMapper(DataMapper[RoleUserInStoreORM, RoleUserInStoreDTO]):
    model = RoleUserInStoreORM
    schema = RoleUserInStoreDTO


class SessionsDataMapper(DataMapper[SessionORM, UserSessionDTO]):
    model = SessionORM
    schema = UserSessionDTO


class UnitsDataMapper(DataMapper[UnitORM, UnitDTO]):
    model = UnitORM
    schema = UnitDTO


class UnitWithMainImageDataMapper(DataMapper[UnitORM, UnitWithMainImageDTO]):
    model = UnitORM
    schema = UnitWithMainImageDTO


class ActionsDataMapper(DataMapper[ActionOrm, ActionDTO]):
    model = ActionOrm
    schema = ActionDTO


class ActionsTransactionsDataMapper(DataMapper[ActionTransactionOrm, ActionTransactionDTO]):
    model = ActionTransactionOrm
    schema = ActionTransactionDTO


class ActionsTransactionsWithUnitDataMapper(
    DataMapper[ActionTransactionOrm, ActionTransactionWithUnitDTO]
):
    model = ActionTransactionOrm
    schema = ActionTransactionWithUnitDTO


class UnitWithActionsDataMapper(DataMapper[UnitORM, UnitWithFieldsDTO]):
    model = UnitORM
    schema = UnitWithFieldsDTO


class ActionWithUnitsTransactionsDataMapper(DataMapper[ActionOrm, ActionWithUnitsTransactionsDTO]):
    model = ActionOrm
    schema = ActionWithUnitsTransactionsDTO


class UnitImagesDataMapper(DataMapper[UnitImageORM, UnitImageDTO]):
    model = UnitImageORM
    schema = UnitImageDTO


class NotificationsDataMapper(DataMapper[NotificationORM, NotificationDTO]):
    model = NotificationORM
    schema = NotificationDTO
