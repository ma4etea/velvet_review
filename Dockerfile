FROM python:3.11.13

# Установка зависимостей для OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Установка Poetry
ENV POETRY_VERSION=2.1.3
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

# Копируем исходный код
COPY . .

CMD ["poetry", "run", "python", "-m", "src.main"]
