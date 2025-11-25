from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class EmailConst:
    subject: str
    template: str


FORGOT_PASSWORD_TEMPLATE = EmailConst("Восстановление пароля", "confirmation_reset_password.html")

CONFIRMATION_EMAIL_TEMPLATE = EmailConst("Регистрация пользователя", "confirmation_email.html")

SUCCESSFUL_REGISTRATION_TEMPLATE = EmailConst(
    "Регистрация пользователя", "successful_registration.html"
)
