def exc_log_string(exc: BaseException) -> str:
    """
    Преобразует исключение в отформатированную строку.

    Args:
        exc (BaseException): Объект исключения.

    Returns:
        str: Строка, содержащая имя класса исключения и сообщение.
    """
    return f"{type(exc).__name__}: {exc}"
