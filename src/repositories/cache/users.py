from src.repositories.cache.base import BaseRepository
from src.repositories.cache.mappers.mappers import UsersMapper
from src.repositories.cache.space_name import space_name_users
from src.schemas.users import UserDTO


class UsersRepository(BaseRepository[UserDTO]):
    space_name = space_name_users
    mapper = UsersMapper

    async def get_user_msgs(self, user_id: int):
        # todo тестовый пример, логика работает.  проверено
        await self.adapter.set("users:1:msgs:1uuid", "Сообщение 1")
        await self.adapter.set("users:1:msgs:2uuid", "Сообщение 2")
        await self.adapter.commit()

        await self.adapter.add_ids_to_list("users:1:msgs:", "1uuid", "2uuid", ttl=3600)
        ids = await self.adapter.get_ids_from_list("users:1:msgs:")
        print(f"{ids=}")
        msgs = await self.adapter.get_all(*[f"users:1:msgs:{id_}" for id_ in ids])

        print(msgs)
        raise ValueError
