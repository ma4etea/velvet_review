from src.exceptions.forbidden import AccessForbiddenException
from src.routers.http_exceptions.base import VelvetHTTPException


class AccessForbiddenHTTPException(VelvetHTTPException):
    details = "Доступ запрещен"
    status_code = 403

    def __init__(self, exc: AccessForbiddenException | None = None):
        detail = exc.details if exc else self.details
        super().__init__(status_code=403, detail=detail)


class CreateStoreForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено создавать store"


class UnitModificationInStoreForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено создавать, изменять, удалять unit в этом store"


class UnitModificationForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено создавать, изменять, удалять этот unit"


class UnitReadInStoreForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено просматривать unit в этом store"


class UnitReadInAllStoresForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено просматривать unit одновременно во всех store"


class ApproveRegistrationForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено подтверждать регистрацию пользователя"


class UpdateRoleInCompanyForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено изменять роль пользователя в компании"


class SelfUpdateRoleInCompanyForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено самому себе изменять роль в компании"


class AssignUserToStoreForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено назначать пользователей в магазин"


class AdminRoleModificationInStoreForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Запрещено изменять роль администратора в магазине"


class ActionAccessForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Доступ запрещен к этой операции"


class StoreAccessForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Access to this store is forbidden"


class AllStoresAccessForbiddenHTTPException(AccessForbiddenHTTPException):
    details = "Access to all stores is forbidden"
