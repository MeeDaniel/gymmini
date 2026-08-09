# Базовый образ Python (pre-release 3.14, так как в pyproject.toml указано >=3.14)
FROM python:3.14-rc-slim

# Копируем бинарники uv из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Устанавливаем рабочую директорию
WORKDIR /app

# Настраиваем переменные окружения: 
# Виртуальное окружение будет создано в /app/.venv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости (без dev-зависимостей, точно по uv.lock)
RUN uv sync --frozen --no-dev

# Копируем исходный код
COPY . .

# Команда запуска
CMD ["python", "main.py"]
