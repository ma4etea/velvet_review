def forgot_key(email: str) -> str:
    """Создает строку уникального ключа в redis
    Например: forgot-example@mail.com"""
    return f"forgot-{email}"
