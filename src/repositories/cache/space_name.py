def space_name_unconfirmed_registration(email: str) -> str:
    return f"auth:unconfirmed_registration:{email}"


def space_name_cooldown_resend_confirm_code(email: str) -> str:
    return f"auth:cooldown_resend_confirm_code:{email}"


def space_name_forgot_password(email: str) -> str:
    return f"auth:forgot_password:{email}"


def space_name_cooldown_forgot_password(email: str) -> str:
    return f"auth:forgot_password:{email}"


space_name_users = "users:"
