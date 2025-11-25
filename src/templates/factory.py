from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template


class TemplateFactory:
    def __init__(self, templates_dir: str):
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.templates_dir = Path(templates_dir)

    def get(self, name: str) -> Template:
        """
        :param name: Название файла шаблона
        """
        path = self.templates_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Файл шаблона '{path}' не найден.")
        return self.env.get_template(name)
