import asyncio
import functools
import inspect
import logging
import os
import sys
import time
from typing import Callable

from src.config import settings

# Создание директории логов
os.makedirs("./logs", exist_ok=True)


class LevelColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",  # Синий
        "INFO": "\033[92m",  # Зелёный
        "WARNING": "\033[93m",  # Жёлтый
        "ERROR": "\033[91m",  # Красный
        "CRITICAL": "\033[95m",  # Фиолетовый
    }

    ALIASES = {
        "uvicorn.access": "uv.access",
        "uvicorn.error": "uv.error",
    }

    RESET = "\033[0m"

    def format(self, record):
        # Цветной уровень
        level_name = record.levelname
        color = self.COLORS.get(level_name, self.RESET)
        colored_level = f"{color}{level_name:<8}{self.RESET}"

        # Псевдоним имени логгера
        alias = self.ALIASES.get(record.name, record.name)

        # Сообщение
        message = record.getMessage()

        # 📌 Для DEBUG добавляем путь и имя функции
        if record.levelno == logging.DEBUG and settings.APP_ENV == "local":
            # relative_path = os.path.relpath(record.pathname, start=os.getcwd())
            # debug_info = f"{relative_path}:{record.lineno} {record.funcName}"
            debug_info = getattr(record, "debug_info", None)
            if debug_info is None:
                relative_path = os.path.relpath(record.pathname, start=os.getcwd())
                debug_info = f"{relative_path}:{record.lineno} {record.funcName}"
            message = f"{message} {color}<- {debug_info}{self.RESET}"

        # Исключения
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            message = f"{message}{record.exc_text}"

        return f"{colored_level} {alias:<10}: {message}"


# Формат для файла — с датой
file_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

# Логгер
logger = logging.getLogger("app")
if settings.APP_ENV == "local":
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# 📁 Запись в файл
file_handler = logging.FileHandler("./logs/app.log", encoding="utf-8")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


if settings.APP_ENV != "prod":
    # 🖥️ Вывод в консоль без даты
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(LevelColorFormatter())
    logger.addHandler(console_handler)
else:
    console_handler = None

for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    uvicorn_logger = logging.getLogger(name)
    uvicorn_logger.handlers.clear()
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_logger.addHandler(file_handler)
    if console_handler:
        uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.propagate = False


# Пример использования
logger.debug("Отладка")
logger.info("Информация")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.critical("Критическая")


def func_debug(func: Callable):
    abs_path = inspect.getsourcefile(func) or "unknown"
    rel_path = os.path.relpath(abs_path, start=os.getcwd())

    try:
        lines, lineno = inspect.getsourcelines(func)
    except OSError:
        lineno = -1  # или другое значение по умолчанию

    func_name = func.__name__

    debug_info = f"{rel_path}:{lineno} {func_name}"

    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logger.debug(f"Calling {func.__name__}({signature}):", extra={"debug_info": debug_info})

            start = time.perf_counter()
            result = await func(*args, **kwargs)
            end = time.perf_counter()

            logger.debug(
                f"{func.__name__} returned {result!r} (took {end - start:.2f} ms)",
                extra={"debug_info": debug_info},
            )
            return result

        return wrapper
    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logger.debug(f"Calling {func.__name__}({signature})", extra={"debug_info": debug_info})

            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()

            logger.debug(
                f"{func.__name__} returned {result!r} (took {end - start:.2f} ms)",
                extra={"debug_info": debug_info},
            )
            return result

        return wrapper
