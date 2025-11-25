from src.exceptions.base import VelvetAppException


class ObjectConflictException(VelvetAppException):
    default_details: str = "Неизвестный конфликт"

    def __init__(self, object_id: int | str | list[str | int] | None = None):
        msg = f"{self.default_details}"
        if object_id is not None:
            msg += f"{object_id}"
        super().__init__(msg)


class IdDuplicateException(ObjectConflictException):
    default_details = "Есть повторяющеюся id: "


class UnitBelongAnotherStoreException(ObjectConflictException):
    default_details = "Unit принадлежит другому store, ids: "


class StoreAlreadyExistsException(ObjectConflictException):
    default_details = "Магазин с таким названием уже существует"
