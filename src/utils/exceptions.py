from typing import Type, Tuple


def is_raise(
    exc: Exception,
    reason: Type[Exception] | Tuple[Type[Exception], ...],
    to_raise: Type[Exception],
    *,
    check_message_contains: tuple[str, ...] | str | None = None,
):
    """
    Проверяет, было ли исходное исключение (`exc`) вызвано ошибкой заданного типа (`reason`)
    внутри цепочки исключений (`__cause__`) и что **все** подстроки из
    `check_message_contains` присутствуют в полном сообщении `exc`.
    Если да — выбрасывает новое исключение (`to_raise`).

    :param exc: Исключение верхнего уровня.
    :param reason: Тип или кортеж типов ошибок для распознавания причины.
    :param to_raise: Исключение, которое будет выброшено.
    :param check_message_contains: Список подстрок | подстрока, которые все должны быть в сообщении ошибки.
    :raise to_raise: Если условия совпадения выполнены.
    """

    if check_message_contains is not None:
        if isinstance(check_message_contains, str):
            check_messages_ = {check_message_contains}
        else:
            check_messages_ = set(check_message_contains)
        full_msg = str(exc).lower()
        # Проверяем, что все подстроки есть в сообщении (регистр не важен)
        if not all(sub.lower() in full_msg for sub in check_messages_):
            return  # Не все подстроки найдены — выходим

    def walk_causes(err: BaseException | None) -> bool:
        seen: set[BaseException | None] = set()
        while err and err not in seen:
            if isinstance(err, reason):
                return True
            seen.add(err)
            err = getattr(err, "__cause__", None)
        return False

    orig = getattr(exc, "orig", None)
    if isinstance(orig, reason) or walk_causes(orig):
        raised_exc = to_raise()
        raise raised_exc from exc
