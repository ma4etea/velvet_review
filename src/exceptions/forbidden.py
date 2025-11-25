from src.exceptions.base import VelvetAppException


class AccessForbiddenException(VelvetAppException):
    default_details = "Доступ запрещен"

    def __init__(self, object_id: int | str | list[str | int] | None = None):
        msg = f"{self.default_details}"
        if object_id is not None:
            msg += f" (id: {object_id})"
        super().__init__(msg)


class UnitModificationInStoreForbiddenException(AccessForbiddenException):
    default_details = "Запрещено создавать, изменять, удалять unit в этом store"


class UnitReadInStoreForbiddenException(AccessForbiddenException):
    default_details = "Запрещено просматривать unit в этом store"


class UnitReadInAllStoresForbiddenException(AccessForbiddenException):
    default_details = "Запрещено просматривать unit одновременно во всех store"


class CreateStoreForbiddenException(AccessForbiddenException):
    default_details = "Запрещено создавать store"


class ActionAccessForbiddenException(AccessForbiddenException):
    default_details = "Доступ запрещен к операции: "


class AllStoresAccessForbiddenException(AccessForbiddenException):
    default_details = "Access to all stores is forbidden"


class StoreAccessForbiddenException(AccessForbiddenException):
    default_details = "Запрещен доступ к store"


class ApproveRegistrationForbiddenException(AccessForbiddenException):
    default_details = "Запрещено подтверждать регистрацию пользователя"


class UpdateRoleInCompanyForbiddenException(AccessForbiddenException):
    default_details = "Запрещено изменять роль пользователя в компании"


class SelfUpdateRoleInCompanyForbiddenException(AccessForbiddenException):
    default_details = "Запрещено самому себе изменять роль в компании"


class AssignUserToStoreForbiddenException(AccessForbiddenException):
    default_details = "Запрещено назначать пользователя в магазин"


class AdminRoleModificationInStoreForbiddenException(AccessForbiddenException):
    default_details = "Запрещено изменять роль администратора в магазине"
