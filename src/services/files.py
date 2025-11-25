from pydantic import TypeAdapter, HttpUrl

from src.config import settings
from src.schemas.files import S3DTO
from src.services.base import BaseService


class FilesService(BaseService):
    @staticmethod
    def get_s3() -> S3DTO:
        domain = TypeAdapter(HttpUrl).validate_python(settings.S3_PUBLIC_URL)
        return S3DTO(domain=domain, bucket=settings.S3_BUCKET)
