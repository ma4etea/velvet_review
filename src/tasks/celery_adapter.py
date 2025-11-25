from typing import Any

from celery import Celery  # type: ignore
from celery.result import AsyncResult  # type: ignore

from src.config import settings

"""
Запуск
celery --app=src.tasks.celery_adapter:celery_app worker --loglevel INFO



celery.conf.update(
    broker_url="redis://localhost:6379/0",
    broker_connection_retry=True,        # включить ретраи (по умолчанию True)
    broker_connection_retry_max=None,    # None = бесконечно
    broker_connection_timeout=30,        # сколько ждать при попытке
)
"""

celery_app = Celery(
    main="tasks",
    broker=settings.REDIS_URL_FOR_TASKS,
    include=["src.tasks.tasks"],
    broker_connection_retry=True,
    broker_connection_retry_max=None,
    broker_connection_timeout=30,
)


def create_celery_task(task_name: str, *args: Any, **kwargs: Any) -> AsyncResult:
    return celery_app.send_task(name=task_name, args=args, kwargs=kwargs)  # type: ignore
