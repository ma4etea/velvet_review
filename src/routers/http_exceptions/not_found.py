from src.exceptions.not_found import ObjectNotFoundException
from src.routers.http_exceptions.base import VelvetHTTPException


class ObjectNotFoundHTTPException(VelvetHTTPException):
    details = "Объект не найден"
    status_code = 404

    def __init__(self, exc: ObjectNotFoundException | None = None):
        detail = exc.details if exc else self.details
        super().__init__(status_code=404, detail=detail)


class UserNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Пользователь не найден"


class UserSessionNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Сессия пользователя не найдена"


class UnitNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Товар не найден"


class UnitImageNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Картинка товара не найдена"


class ActionNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Действие не найдено"


class StoreNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Store не найдена"


class UnconfirmedRegistrationNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Заявку на регистрацию не удалось найти"


class NotificationNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Уведомления для пользователя не найдены"


class RoleUserInStoreNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Пользователю не назначена роль в этом магазине"


class DownloadFileNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Файл не найден"


class ForgotPasswordNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Заявка на сброс пароля не найдена"


class DeviceIDNotFoundHTTPException(ObjectNotFoundHTTPException):
    details = "Device ID не найден в cookies"
