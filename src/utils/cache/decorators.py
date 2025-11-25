import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar

from src.logging_config import logger
from src.schemas.base import BaseSchema
from src.services.base import BaseService

DTOType = TypeVar("DTOType", bound=BaseSchema)


def cache_service_method_by_id(
    return_type: type[DTOType],
    ttl: int = 60,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for caching service methods that return DTOs by ID.

    This decorator is designed to cache the results of service methods that return DTOs
    based on an ID parameter. It stores the serialized DTO in a cache using a key pattern:
    'cached_method:{service_class}:{method_name}:{id}'

    :param return_type: The DTO class type that will be returned by the decorated method
    :param ttl: Time to live in seconds for the cached value (default: 60 seconds)
    :return: Decorated function that will check cache before executing the original method
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("cached supports async functions only")

        @wraps(func)
        async def wrapper(self: BaseService, *args: int, **kwargs: int) -> DTOType:
            id_ = args[0] if args else next(iter(kwargs.values()))
            key = f"cached_method:{func.__qualname__}:{id_}"
            result = await self.cache.adapter.get_one_or_none(key=key)
            if result:
                dto = return_type.model_validate_json(result)
                logger.debug(f"dto из кеша: {return_type.__name__}")
                return dto
            else:
                dto: DTOType = await func(self, id_)
                await self.cache.adapter.set(key=key, value=dto.model_dump_json(), ttl=ttl)
                await self.cache.adapter.commit()
                logger.debug(f"dto из базы данных: {return_type.__name__}")
                return dto

        return wrapper

    return decorator
