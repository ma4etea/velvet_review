from collections import defaultdict
from typing import Type, Any

from src.routers.http_exceptions.base import VelvetHTTPException


import re

from src.schemas.base import ErrorResponse


def pascal_to_words(name: str) -> str:
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", name)


def exceptions_to_openapi(
    *http_exceptions: Type[VelvetHTTPException],
) -> dict[int | str, dict[str, Any]]:
    """
    Создает swagger документацию для http исключений.
    Возвращает responses для FastAPI со списком вариантов ошибок для каждого status_code.
    :param http_exceptions: Список Исключений
    :return: возможные исключения для FastAPI документации
    """

    grouped: dict[int, list[Type[VelvetHTTPException]]] = defaultdict(list)
    for http_exc in http_exceptions:
        grouped[http_exc.status_code].append(http_exc)

    responses: dict[int | str, dict[str, Any]] = {}
    for code, exc_list in grouped.items():
        examples = {}
        for http_exc in exc_list:
            error_name = pascal_to_words(http_exc.__name__.removesuffix("HTTPException"))
            examples[error_name] = {
                "value": ErrorResponse(status_code=http_exc.status_code, detail=http_exc.details)
            }

        responses[code] = {
            "model": ErrorResponse,
            "description": f"{len(exc_list)} possible errors",
            "content": {
                "application/json": {
                    "examples": examples,
                }
            },
        }

    return responses
