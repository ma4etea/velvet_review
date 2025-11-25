from datetime import datetime, timezone, timedelta

from src.config import settings


def get_utc_now() -> datetime:
    """Возвращает текущую дату и время в UTC (timezone-aware)"""
    return datetime.now(timezone.utc)


def get_expiration_refresh_token() -> datetime:
    """
    Возвращает дату и время истечения срока действия refresh токена.

    Время рассчитывается как текущий момент в UTC плюс количество дней,
    заданное в настройке `JWT_REFRESH_TOKEN_EXPIRE_DAYS`.

    Returns:
        datetime: Дата и время истечения срока действия токена в UTC.
    """
    return datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
