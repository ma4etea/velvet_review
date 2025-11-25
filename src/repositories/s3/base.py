from src.adapters.s3_adapter import S3Adapter


class BaseRepository:
    def __init__(self, adapter: S3Adapter):
        self.adapter = adapter

    async def add(self, src_file_path: str, bucket: str, key: str):
        try:
            await self.adapter.upload_file(src_file_path, bucket, key)
        except:
            raise

    async def delete(self, bucket: str, keys: tuple[str, ...]):
        try:
            await self.adapter.delete(bucket=bucket, keys=keys)
        except:
            raise
