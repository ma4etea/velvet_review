from src.tasks.celery_adapter import create_celery_task


class TaskManager:
    @staticmethod
    def celery_test(arg1: int, arg2: str):
        return create_celery_task("celery_test", **locals())

    @staticmethod
    def send_confirm_code_to_email(to_email: str, confirm_code: str, template_html: str):
        """
        :param to_email: На какой imail отправить.
        :param confirm_code: Код подтверждения
        :param template_html: Шаблон письма
        """
        return create_celery_task("send_confirm_code_to_email", **locals())

    @staticmethod
    def send_msg_to_email(
        to_email: str, subject: str, template_filename: str, **template_variables: str
    ):
        """
        :param to_email: На какой email отправить.
        :param subject: Тема письма
        :param template_filename: Путь к шаблону html
        :param template_variables: Аргументы для шаблона ninja2
        """
        return create_celery_task(
            "send_msg_to_email", to_email, subject, template_filename, **template_variables
        )

    @staticmethod
    def saving_resized_unit_images_in_s3(
        unit_images_ids: list[int],
        src_path: str,
        unit_id: int,
        sizes: tuple[int, ...] = (1280, 300, 100),
    ):
        return create_celery_task("saving_resized_unit_images_in_s3", **locals())


task_manager = TaskManager
# test = task_manager.celery_test(1, "we")
