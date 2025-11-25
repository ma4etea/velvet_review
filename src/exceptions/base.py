class VelvetAppException(Exception):
    details = "Неизвестная ошибка"

    def __init__(self, details: str | None = None):
        if details:
            self.details = details
        super().__init__(self.details)

    def __str__(self):
        return self.details


class ObjectWrongException(VelvetAppException):
    default_details = "Объект не верный"

    def __init__(self, details: str | None = None):
        self.details = details or self.default_details
        super().__init__(self.details)


class NotAnAccessTokenException(ObjectWrongException):
    default_details = "Не является access-token"


class NotARefreshTokenException(ObjectWrongException):
    default_details = "Не является refresh-token"


class ExpiredSignatureException(VelvetAppException):
    details = "Токен истек"


class ExpiredConfirmCodeException(VelvetAppException):
    details = "Код подтверждения истек"


class InvalidSignatureException(VelvetAppException):
    details = "Неверная подпись токена"


class UserAlreadyExistsException(VelvetAppException):
    details = "Пользователь уже существует"


class UnconfirmedRegistrationAlreadyExistsException(VelvetAppException):
    details = "Существует неподтвержденная регистрация. Запросите код подтверждения повторно"


class ResendLimitAlreadyExistsException(VelvetAppException):
    details = "Стоит лимит на запрос кода подтверждения"


class CooldownForgotAlreadyExistsException(VelvetAppException):
    details = "Стоит лимит на запрос кода для сброса пароля"


class ToBigIdException(VelvetAppException):
    details = "ID превышает допустимое значение"


class TypeErrorException(VelvetAppException):
    pass


class ObjectAlreadyExistsException(VelvetAppException):
    details = "Объект уже существует"


class StmtSyntaxErrorException(VelvetAppException):
    details = "Синтаксическая ошибка в SQL-запросе"


class NotNullViolationException(VelvetAppException):
    details = "Нарушение ограничения NOT NULL"


class OffsetToBigException(VelvetAppException):
    details = "Слишком большой offset для запроса"


class LimitToBigException(VelvetAppException):
    details = "Слишком большой limit для запроса"


class ObjectUseAsForeignKeyException(VelvetAppException):
    details = "Объект связан внешним ключом и не может быть удалён"


class UnitHaveTransactionsException(VelvetAppException):
    details = "Unit имеет транзакции"


class InvalidPasswordException(VelvetAppException):
    details = "Неверные пароль"


class InvalidConfirmCodeException(VelvetAppException):
    details = "Неверные код подтверждения"


class DbIsNotAvailableException(VelvetAppException):
    details = "База данных не доступна>"


class RedisIsNotAvailableException(VelvetAppException):
    details = "Редис не доступен>"


class ForeignKeyViolationException(VelvetAppException):
    details = "Ошибка внешнего ключа"


class EmptyIterableException(VelvetAppException):
    details = "Требуется хотя бы один элемент"


class UnitOutOfStockException(VelvetAppException):
    details = "Недостаточное количество товара "


class UnitImagesLimitException(VelvetAppException):
    details = "Максимальное количество загруженных изображений для unit"


class ObjectNotUniqueException(VelvetAppException):
    details = "Объект не уникальный, результат имеет более одного элемента"


class UnitImageIsMainException(VelvetAppException):
    details = "Image является главной картинкой для товара"


class RoleUserInStoreAlreadyExistsException(VelvetAppException):
    details = "Роль пользователя для магазина уже существует"


class ServiceDatabaseNotInitializedException(VelvetAppException):
    details = "База данных сервиса не инициализирована"


class ServiceCacheNotInitializedException(VelvetAppException):
    details = "Кэш сервиса не инициализирована"


class ServiceS3NotInitializedException(VelvetAppException):
    details = "S3 сервиса не инициализирована"


class UnexpectedTypeException(VelvetAppException):
    details = "Неожиданный тип исключение"


class DeviceMismatchException(VelvetAppException):
    details = "Device ID не соответствует сессии"
