from src.exceptions.base import (
    ServiceDatabaseNotInitializedException,
    ServiceCacheNotInitializedException,
    ServiceS3NotInitializedException,
)
from src.utils.cache.manager import CacheManager
from src.utils.db_manager import DBAsyncManager
from src.utils.s3_manager import S3Manager


class BaseService:
    _db: DBAsyncManager | None
    _cache: CacheManager | None
    _s3: S3Manager | None

    def __init__(
        self,
        db: DBAsyncManager | None = None,
        cache: CacheManager | None = None,
        s3: S3Manager | None = None,
    ):
        self._db = db
        self._cache = cache
        self._s3 = s3

    @property
    def db(self) -> DBAsyncManager:
        if self._db is None:
            raise ServiceDatabaseNotInitializedException
        return self._db

    @property
    def cache(self) -> CacheManager:
        if self._cache is None:
            raise ServiceCacheNotInitializedException
        return self._cache

    @property
    def s3(self) -> S3Manager:
        if self._s3 is None:
            raise ServiceS3NotInitializedException
        return self._s3
