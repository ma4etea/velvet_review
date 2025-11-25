from fastapi import APIRouter

from src.schemas.base import StandardResponse
from src.schemas.files import S3Response
from src.services.files import FilesService
from src.utils.files import get_md

files_router = APIRouter(prefix="/files", tags=["Файлы"])


@files_router.get(
    "/s3",
    description=get_md("docs/get_s3_domain_description.md"),
    response_model=StandardResponse[S3Response],
)
async def get_s3() -> StandardResponse[S3Response]:
    s3 = FilesService.get_s3()
    return StandardResponse(data=S3Response(s3=s3), message=f"{s3.domain}{s3.bucket}/")
