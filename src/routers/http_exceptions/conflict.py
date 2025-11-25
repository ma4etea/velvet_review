from src.routers.http_exceptions.base import VelvetHTTPException


class UserAlreadyExistsHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Пользователь уже существует"


class UnitHaveTransactionsHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Unit имеет транзакции"


class UnitImagesLimitHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Превышено максимальное количество изображений для Unit"


class UnconfirmedRegistrationAlreadyExistsHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Заявка на регистрацию уже существует"


class RoleUserInStoreAlreadyExistsHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Пользователю уже назначена роль в магазине"


class UnitOutOfStockHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Недостаточное количество товара"


class ResendLimitAlreadyExistsHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Код уже отправлен, попробуете позже"


class CooldownForgotAlreadyExistsHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Код уже отправлен, попробуете позже"


class StoreAlreadyExistsHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Магазин с таким названием уже существует"


class UnitImageIsMainHTTPException(VelvetHTTPException):
    status_code = 409
    details = "Изображение является главным для товара"
