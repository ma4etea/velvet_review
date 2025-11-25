from src.exceptions.not_found import ObjectNotFoundException, UnitImageNotFoundException
from src.schemas.unit_images import UnitImageDTO
from src.services.base import BaseService


class UnitImagesService(BaseService):
    async def check_get_unit_image(self, unit_id: int, image_id: int) -> UnitImageDTO:
        """
        Проверить существования картинки у товара. Картинка строго привязана к одному товару.
        :param unit_id: Id товара.
        :param image_id: Id картинки.
        :return: Dto картинки
        :raise UnitImageNotFoundException: Если картинка не найдена у товара
        """
        try:
            return await self.db.unit_images.get_one(id=image_id, unit_id=unit_id)
        except ObjectNotFoundException as exc:
            raise UnitImageNotFoundException from exc
