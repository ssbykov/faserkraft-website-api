FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry-cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

# Отдельный слой зависимостей: Docker не будет переустанавливать их,
# пока pyproject.toml и poetry.lock не изменятся.
COPY pyproject.toml poetry.lock ./

# --no-root: само приложение не устанавливается как Python-пакет,
# код ниже будет доступен через COPY . .
RUN poetry install --only main --no-root \
    && rm -rf $POETRY_CACHE_DIR

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]