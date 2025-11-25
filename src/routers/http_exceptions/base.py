from fastapi import HTTPException

from src.schemas.base import ErrorResponse, ValidationErrorResponse


class VelvetHTTPException(HTTPException):
    status_code = 500
    details = "Ошибка сервера"

    def __init__(self, *, status_code: int | None = None, detail: str | None = None):
        status_code = status_code or self.status_code
        detail = detail or self.details
        super().__init__(status_code=status_code, detail=detail)

    @classmethod
    def responses(cls):
        return {
            cls.status_code: {
                "model": ErrorResponse,
                "description": cls.details,
                "content": {
                    "application/json": {
                        "example": {"status_code": cls.status_code, "detail": cls.details}
                    }
                },
            }
        }


class ToBigIdHTTPException(VelvetHTTPException):
    def __init__(self, detail: str = "ИД слишком большой"):
        if detail:
            self.detail = detail

    status_code = 400
    details = "ИД слишком большой"


class InvalidCredentialsHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Неверные логин и/или пароль"


class InvalidConfirmCodeHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Неверный код подтверждения"


class InvalidTokenHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Токен отсутствует"


class IncorrectTokenHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Неверный токен"


class ExpiredTokenHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Токен истек"


class ExpiredConfirmCodeHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Код подтверждения истек"


class NotAnAccessTokenHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Не является access-token"


class NotARefreshTokenHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Не является refresh-token"


class DeviceMismatchHTTPException(VelvetHTTPException):
    status_code = 401
    details = "Устройство не соответствует сессии пользователя."


class StmtSyntaxErrorHTTPException(VelvetHTTPException):
    status_code = 400
    details = "Ошибка запроса"


class NotNullViolationHTTPException(VelvetHTTPException):
    status_code = 400
    details = "Значение не может быть null"


class UnsupportedImageExtensionHTTPException(VelvetHTTPException):
    status_code = 400
    details = "Не верное расширение изображения"


class OffsetToBigHTTPException(VelvetHTTPException):
    status_code = 422
    details = "Превышено максимальное значение page"


class LimitToBigHTTPException(VelvetHTTPException):
    status_code = 422
    details = "Превышено максимальное значение per_page"


class InvalidPaginationHTTPException(VelvetHTTPException):
    status_code = 422
    details = "Неверные данные пагинации"


# todo скорее всего этот класс не понадобится в будущем
class PydanticValidationErrorHTTPException(VelvetHTTPException):
    status_code = 422
    details = "Ошибка валидации данных"

    @classmethod
    def responses(cls):  # type: ignore
        return {
            cls.status_code: {
                "model": ValidationErrorResponse,
                "description": cls.details,
            }
        }


class PatchFieldValidationHTTPException(PydanticValidationErrorHTTPException):
    details = "Нужно передать хотя бы одно поле"


class PatchUnitFieldValidationHTTPException(PydanticValidationErrorHTTPException):
    details = "Некоторые поля не могу быть null"


class MaskedApplicationErrorHTTPException(VelvetHTTPException):
    status_code = 400
    details = "Не удалось обработать запрос. Повторите позже."


class SalesValidationHTTPException(PydanticValidationErrorHTTPException):
    details = "Не все поля для sales переданы верно"


class UnitIdsDuplicateHTTPException(PydanticValidationErrorHTTPException):
    details = "unitId имеет дубликаты"
