from src.repositories.s3.base import BaseRepository
from src.schemas.unit_images import UnitImageDTO


class UnitImagesRepository(BaseRepository):
    async def add_unit_image(self, src_file_path: str, key: str) -> str:
        await self.add(src_file_path=src_file_path, bucket="velvet", key=key)
        return key

    async def delete_unit_image(self, dto: UnitImageDTO):
        keys = tuple(filter(None, (dto.key_100, dto.key_300, dto.key_1280)))
        await self.delete(bucket="velvet", keys=keys)
