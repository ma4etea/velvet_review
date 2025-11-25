from src.adapters.redis_adapter import redis_for_fastapi_cache, redis_adapter, redis_client
from src.logging_config import logger
from src.schemas.types import AppEnv
from src.utils.fastapi_startup import load_placeholders_in_s3

# todo logger.info("main.py инициализируется два раза , нормально ли?")

from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.config import settings

from src.routers.base import public_router, protected_router
from src.routers.http_exceptions.handlers.base import (
    args_http_exception_handler,
    args_validation_exception_handler,
    args_internal_server_error_handler,
    args_masked_app_db_error_handler,
    args_masked_app_redis_error_handler,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # await run_task_check_redis()

    await load_placeholders_in_s3()

    try:
        if settings.APP_ENV == AppEnv.local or settings.APP_ENV == AppEnv.dev:
            await redis_client.flushdb()

        FastAPICache.init(RedisBackend(redis_for_fastapi_cache), prefix="fastapi-cache")
        logger.info("FastAPICache успешно инициализирован с Redis клиентом")

    except:
        raise

    yield
    await redis_for_fastapi_cache.aclose()
    await redis_adapter.close()


app = FastAPI(lifespan=lifespan, root_path=settings.ROOT_PATH)

app.include_router(public_router)
app.include_router(protected_router)


app.add_exception_handler(*args_validation_exception_handler)
app.add_exception_handler(*args_http_exception_handler)
app.add_exception_handler(*args_internal_server_error_handler)
app.add_exception_handler(*args_masked_app_db_error_handler)
app.add_exception_handler(*args_masked_app_redis_error_handler)


if settings.APP_ENV == AppEnv.local:
    if __name__ == "__main__":
        uvicorn.run(
            "src.main:app", host=settings.APP_HOST, reload=False, workers=None, log_config=None
        )
elif settings.APP_ENV == AppEnv.dev:
    if __name__ == "__main__":
        uvicorn.run(
            "src.main:app", host=settings.APP_HOST, reload=False, workers=None, log_config=None
        )
elif settings.APP_ENV == AppEnv.prod:
    if __name__ == "__main__":
        uvicorn.run(
            "src.main:app", host=settings.APP_HOST, reload=False, workers=None, log_config=None
        )
