from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.repositories.db.actions import ActionsTransactionsRepository, ActionsRepository
from src.repositories.db.notifications import NotificationsRepository
from src.repositories.db.stores import StoresRepository, RoleUserInStoreRepository
from src.repositories.db.units import UnitsRepository
from src.repositories.db.users import UsersRepository, SessionsRepository
from src.repositories.db.images import UnitImagesRepository
from types import TracebackType


class DBAsyncManager:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()

        self.users = UsersRepository(self.session)
        self.role_user_in_store = RoleUserInStoreRepository(self.session)
        self.stores = StoresRepository(self.session)

        self.user_sessions = SessionsRepository(self.session)
        self.units = UnitsRepository(self.session)
        self.actions = ActionsRepository(self.session)
        self.actions_transactions = ActionsTransactionsRepository(self.session)
        self.unit_images = UnitImagesRepository(self.session)
        self.notifications = NotificationsRepository(self.session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
