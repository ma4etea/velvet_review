from typing import Union, Any

from sqlalchemy import Select, Update, Insert, Delete

from src.database import engine

StmtType = Union[Select[Any], Update, Insert, Delete]


def sql_debag(stmt: StmtType) -> str:
    """
    Компилирует SQLAlchemy-выражение в строку SQL с подставленными значениями.

    Args:
        stmt: SQLAlchemy выражение (например, select(), insert(), update()).

    Returns:
        str: Скомпилированный SQL-запрос со всеми значениями, подставленными напрямую в текст запроса.
    """
    return str(stmt.compile(bind=engine, compile_kwargs={"literal_binds": True}))
