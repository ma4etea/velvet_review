from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_400_BAD_REQUEST,
)

from src.exceptions.base import (
    DbIsNotAvailableException,
    RedisIsNotAvailableException,
    UnexpectedTypeException,
)
from src.schemas.base import ValidationErrorResponse, ErrorResponse

"""
- Модуль содержит обработчики исключений (exception handlers), используемые в приложении FastAPI.

- FastAPI при вызове обработчика всегда передаёт два аргумента:
  - `request`: экземпляр `Request`, в контексте которого произошло исключение;
  - `exc`: экземпляр исключения.

- Поэтому сигнатура всех handlers должна соответствовать шаблону:
    async def handler(request: Request, exc: Exception) -> Response

- Хотя аннотация типа `exc: Exception` указывает на базовый тип, 
  каждый конкретный обработчик предназначен для определённого наследника `Exception` 
  (например, `RequestValidationError`). 
  
- Если в handler передано исключение другого типа, это обычно свидетельствует 
  о неправильной регистрации или использовании обработчика.
"""


async def validation_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Исключение pydantic валидации преобразует в ValidationErrorResponse"""
    if isinstance(exc, RequestValidationError):
        response_data = ValidationErrorResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
        )
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=response_data.model_dump(mode="json")
        )
    else:
        raise UnexpectedTypeException


args_validation_exception_handler = (RequestValidationError, validation_exception_handler)


async def http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Любой HTTPException преобразует в ErrorResponse"""
    if isinstance(exc, HTTPException):
        response_data = ErrorResponse(
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code, content=response_data.model_dump(mode="json")
        )
    else:
        raise UnexpectedTypeException


args_http_exception_handler = (HTTPException, http_exception_handler)


async def masked_app_error_handler(_: Request, __: Exception) -> JSONResponse:
    """
    - Обработчик внутренних ошибок приложения, замаскированный для клиента.
    :return: Возвращает общее сообщение об ошибке без раскрытия деталей внутреннего состояния
    """
    response_data = ErrorResponse(
        status_code=HTTP_400_BAD_REQUEST, detail="Не удалось обработать запрос. Повторите позже."
    )
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST, content=response_data.model_dump(mode="json")
    )


args_masked_app_db_error_handler = (DbIsNotAvailableException, masked_app_error_handler)
args_masked_app_redis_error_handler = (RedisIsNotAvailableException, masked_app_error_handler)


async def internal_server_error_handler(_: Request, __: Exception) -> JSONResponse:
    """
    - Глобальный обработчик не перехваченных исключений.
    - Преобразует любые неожиданные ошибки приложения в стандартный JSON-ответ
      формата `ErrorResponse` с кодом 500, не раскрывая детали внутреннего состояния.
    - Используется как **fallback** ("последняя линия обороны").
    """

    response_data = ErrorResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера"
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=response_data.model_dump(mode="json")
    )


args_internal_server_error_handler = (Exception, internal_server_error_handler)
