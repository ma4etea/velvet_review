from pydantic import HttpUrl

from src.schemas.base import BaseSchema


class S3DTO(BaseSchema):
    domain: HttpUrl
    bucket: str


class Placeholders(BaseSchema):
    error_100: str = "placeholders/100/error.jpg"
    error_300: str = "placeholders/300/error.jpg"
    error_1280: str = "placeholders/1280/error.jpg"


class S3Response(BaseSchema):
    s3: S3DTO
    placeholders: Placeholders = Placeholders()
