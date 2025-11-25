import asyncio
from pathlib import Path
from time import sleep

from jinja2 import UndefinedError
from email.message import EmailMessage
import smtplib

from src.database import new_async_session_null_pool
from src.services.units import UnitsService
from src.tasks.celery_adapter import celery_app
from src.config import settings
from src.logging_config import logger

from src.templates import template_factory
from src.utils.db_manager import DBAsyncManager
from src.utils.files import remove_tree
from src.utils.images import resized_images
from src.utils.s3_manager import get_s3_manager_fabric

"""
Celery загружает таски из этого файла.
При добавлении новых, нужно продублировать название функции и аргументы в TaskManager
Метод TaskManager.test() должен соответствовать 
    зарегистрированному названию @celery_inst.task(name="test")
"""

# def get_template(path_to_template_html: str) -> Template:
#     """
#     :param path_to_template_html: путь к шаблону html
#     :return: объект шаблона Jinja2
#     """
#     path = Path("src/templates") / Path(path_to_template_html).name
#     if not path.exists():
#         raise FileNotFoundError(f"Файл шаблона html не найден: {path}")
#
#     env = Environment(undefined=StrictUndefined, loader=FileSystemLoader(str(path.parent)))
#     template = env.get_template(path.name)
#     return template


@celery_app.task(name="saving_resized_unit_images_in_s3")  # type: ignore
def saving_resized_unit_images_in_s3(
    unit_images_ids: list[int],
    src_path: str,
    unit_id: int,
    sizes: tuple[int, ...] = (1280, 300, 100),
):
    """

    :param unit_images_ids: Список id изображений, которые уже созданы в db со статусом pending
    :param src_path: Папка источник файлов
    :param unit_id:
    :param sizes: нужные размеры файлов
    :return:

    from contextlib import AsyncExitStack

    async with AsyncExitStack() as stack:
    db = await stack.enter_async_context(get_db())
    s3 = await stack.enter_async_context(get_s3())
    cache = await stack.enter_async_context(get_cache())
    # тут используем db, s3, cache
    ...
    """
    folder = Path(src_path)
    files_paths = [str(folder / f.name) for f in folder.iterdir() if f.is_file()]
    resized_paths: list[dict[int, str] | None] = []
    for file_path in files_paths:
        resized_paths.append(
            resized_images(*sizes, src_file_path=file_path, dst_folder_path=src_path)
        )

    async def main():
        async with get_s3_manager_fabric() as s3:
            async with DBAsyncManager(new_async_session_null_pool) as db:
                await UnitsService(db=db, s3=s3).upload_unit_images_in_s3(
                    unit_images_ids=unit_images_ids,
                    resized_files_path=resized_paths,
                    unit_id=unit_id,
                )

    try:
        asyncio.run(main())
    except Exception as exc:
        logger.warning(exc, exc_info=True)
    finally:
        remove_tree(Path(src_path))  # todo сделать крон на переодическое удаление


# @celery_app.task(name="send_confirm_code_to_email")
# def send_confirm_code_to_email(to_email: str, confirm_code: str, template_html: str):
#     if str(to_email).__contains__("@example.com"):
#         logger.debug(f"Запрос кода на тестовую почту @example.com. Код:{confirm_code}")
#         return
#     env = Environment(loader=FileSystemLoader(str(templates_dir)))
#     template = env.get_template(template_html)
#     html_content = template.render(code=confirm_code)
#
#     message = EmailMessage()
#     message.set_content("Ваш почтовый клиент не поддерживает HTML")
#     message.add_alternative(html_content, subtype="html")
#     message["From"] = settings.email_settings.EMAIL_USERNAME
#     message["To"] = to_email
#     message["Subject"] = "Подтверждение регистрации"
#
#     with smtplib.SMTP_SSL(
#             host=settings.email_settings.EMAIL_HOST,
#             port=settings.email_settings.EMAIL_PORT
#     ) as smtp:
#         smtp.login(
#             user=settings.email_settings.EMAIL_USERNAME,
#             password=settings.email_settings.EMAIL_PASSWORD.get_secret_value(),
#         )
#         smtp.send_message(msg=message)


@celery_app.task(name="send_msg_to_email")  # type: ignore
def send_msg_to_email(
    to_email: str, subject: str, template_filename: str, **template_variables: str
):
    if str(to_email).__contains__("@example.com"):
        logger.debug(f"Запрос кода на тестовую почту @example.com. Код:{template_variables}")
        return

    template = template_factory.get(template_filename)
    try:
        html_content = template.render(**template_variables)
    except UndefinedError as exc:
        raise ValueError(
            f"Не верные переменные: { {k: '*****' for k in template_variables.keys()} }."
            f" Для html шаблона: {template_filename}"
        ) from exc

    message = EmailMessage()
    message.set_content("Ваш почтовый клиент не поддерживает HTML")
    message.add_alternative(html_content, subtype="html")
    message["From"] = settings.email_settings.EMAIL_USERNAME
    message["To"] = to_email
    message["Subject"] = subject

    with smtplib.SMTP_SSL(
        host=settings.email_settings.EMAIL_HOST, port=settings.email_settings.EMAIL_PORT
    ) as smtp:
        smtp.login(
            user=settings.email_settings.EMAIL_USERNAME,
            password=settings.email_settings.EMAIL_PASSWORD.get_secret_value(),
        )
        smtp.send_message(msg=message)


@celery_app.task(name="celery_test")  # type: ignore
def celery_test(arg1: int, arg2: str) -> None:
    sleep(1)
    print(f"Тест, {arg1} {arg2}")
