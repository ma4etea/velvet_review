from src.models.units import UnitImageORM
from src.repositories.db.mappers.mappers import UnitImagesDataMapper
from src.repositories.db.base import BaseRepository
from src.schemas.unit_images import UnitImageDTO


class UnitImagesRepository(BaseRepository[UnitImageORM, UnitImageDTO]):
    model = UnitImageORM
    mapper = UnitImagesDataMapper
