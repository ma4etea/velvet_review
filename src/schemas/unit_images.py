from src.models.units import UnitImageStatusEnum
from src.schemas.base import BaseSchema
from src.schemas.types import IDInt, S3Key
from src.schemas.mixin import PatchValidatorMixin


class AddUnitImageDTO(BaseSchema):
    unit_id: IDInt
    key_100: S3Key | None = None
    key_300: S3Key | None = None
    key_1280: S3Key | None = None
    status: UnitImageStatusEnum


class EditUnitImageDTO(PatchValidatorMixin, BaseSchema):
    status: UnitImageStatusEnum | None = None
    key_100: S3Key | None = None
    key_300: S3Key | None = None
    key_1280: S3Key | None = None


class UnitImageDTO(BaseSchema):
    id: IDInt
    unit_id: IDInt
    key_100: S3Key | None
    key_300: S3Key | None
    key_1280: S3Key | None
    status: UnitImageStatusEnum
