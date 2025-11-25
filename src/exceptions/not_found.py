from src.exceptions.base import VelvetAppException


class ObjectNotFoundException(VelvetAppException):
    object_name: str = "Объект"

    def __init__(self, object_id: int | str | list[str | int] | None = None):
        msg = f"{self.object_name} не удалось найти."
        if object_id is not None:
            msg += f" (id: {object_id})"
        super().__init__(msg)


class UserNotFoundException(ObjectNotFoundException):
    object_name = "Пользователь"


class AllUnitsNotFoundException(ObjectNotFoundException):
    object_name = "Все товары"


class UnitNotFoundException(ObjectNotFoundException):
    object_name = "Товар"


class ActionNotFoundException(ObjectNotFoundException):
    object_name = "Действие"


class UserSessionNotFoundException(ObjectNotFoundException):
    object_name = "Сессия пользователя"


class StoreNotFoundException(ObjectNotFoundException):
    object_name = "Store"


class UnconfirmedRegistrationNotFoundException(ObjectNotFoundException):
    object_name = "Неподтвержденную регистрацию"


class ForgotPasswordNotFoundException(ObjectNotFoundException):
    object_name = "Заявку на сброс забытого пароля"


class UnitImageNotFoundException(ObjectNotFoundException):
    object_name = "Изображение для товара"


class ForeignKeyNotFoundException(ObjectNotFoundException):
    object_name = "Внешний ключ"


class NotificationNotFoundException(ObjectNotFoundException):
    object_name = "Уведомления для пользователя"


class UsersCanApprovingRegistrationNotFoundException(ObjectNotFoundException):
    object_name = "Пользователя который может подтвердить регистрацию"


class RoleUserInStoreNotFoundException(ObjectNotFoundException):
    object_name = "Роль пользователя в магазине не найдена"


class RefreshTokenNotFoundException(ObjectNotFoundException):
    object_name = "Refresh токен"


class DeviceIDNotFoundException(ObjectNotFoundException):
    object_name = "Device ID"
