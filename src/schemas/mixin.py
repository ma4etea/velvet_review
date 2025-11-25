import re

from pydantic import model_validator, field_validator

from src.routers.http_exceptions.base import PatchFieldValidationHTTPException
from src.schemas.base import BaseSchema
from src.schemas.types import Password


class PasswordMixin(BaseSchema):
    """
    Миксин предназначен для проверяет поле password на соответствие условиям.
    """

    password: Password

    @field_validator("password", mode="before")  # noqa ✅ Валидация pedantic!
    @classmethod
    def validate_password(cls, password: str) -> str:
        """
        Проверяет, что пароль:
        - содержит хотя бы 1 заглавную букву
        - содержит хотя бы 1 строчную букву
        - содержит хотя бы 1 цифру
        - содержит хотя бы 1 специальный символ (!@#$%^&* и т. д.)
        """
        if not re.search(r"[A-Z]", password):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[a-z]", password):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r"\d", password):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ (!@#$%^&*)")
        return password


class PatchValidatorMixin(BaseSchema):
    """
    Миксин для Pydantic-моделей, предназначенных для PATCH-запросов.

    Цель миксина — гарантировать, что при частичном обновлении (PATCH)
    клиент передаёт хотя бы одно поле.

    Если в запросе не передано ни одного поля (модель пуста),
    будет выброшено исключение HTTP 422 с сообщением:

        "Нужно передать хотя бы одно поле"

    Это позволяет избежать бессмысленных PATCH-запросов без содержимого.

    Пример использования:

    ```python
    class EditRoom(PatchValidatorMixin):
        title: str = None
        description: str | None = None
    ```

    ```json
    {} # ❌ вызовет HTTPException 422
    {title="Новый заголовок"} # ✅ корректно
    {description="Новое описание"} # ✅ корректно
    ```

    Замечание:
    - Поля должны иметь значение по умолчанию `None`, чтобы быть опциональными.
    - Эта проверка выполняется после всех остальных валидаторов Pydantic.

    """

    @model_validator(mode="after")
    def at_least_one_non_null(self):
        data = self.model_dump(exclude_unset=True)

        if not data:
            raise PatchFieldValidationHTTPException
        return self

    # todo на этом этапе можно реализовать exclude_unset=True и exclude_none=True
    #  self.model_validate(data) что бы убрать не переданные и None поля и сразу получить готовую схему для репозитория
