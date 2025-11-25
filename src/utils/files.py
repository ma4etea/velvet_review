from pathlib import Path

from jinja2 import Template


def remove_tree(path: Path):
    """
    Удаляет рекурсивно папку
    :param path: путь в папке
    """
    for item in path.iterdir():
        if item.is_dir():
            remove_tree(item)
        else:
            item.unlink()
    path.rmdir()


def get_md(path_to_md_file: str, **template_vars: str) -> str:
    """
    :param path_to_md_file: путь из папки src/routers
    :param template_vars: словарь переменных для подстановки в Markdown
    :return: текст из md файла с подставленными переменными
    """
    md_path = Path("src/routers") / path_to_md_file
    md_text = md_path.read_text(encoding="utf-8")

    # Подставляем переменные через Jinja2
    template = Template(md_text)
    result = template.render(**template_vars)
    return result
