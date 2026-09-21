# Faserkraft Website API

Backend (FastAPI + PostgreSQL) для нового корпоративного сайта Faserkraft,
создан в рамках миграции с устаревшего WordPress (WordPress 5.7.18, тема Inovado/Minti).

## Стек

- FastAPI + SQLAlchemy 2.x (async) + PostgreSQL
- Alembic для миграций
- JWT-аутентификация для админ-части
- Docker Compose (api + PostgreSQL + MinIO для файлов)

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d --build
```

API будет доступен на http://localhost:8000, документация — на http://localhost:8000/api/v1/docs.

## Импорт данных из старого сайта

В legacy_data/ лежат уже разобранные данные из WordPress-каталога продукции.

```bash
docker compose exec api python -m scripts.import_legacy_data
```

## Структура проекта

```
app/
  core/       — конфигурация (.env)
  db/         — подключение к PostgreSQL
  models/     — SQLAlchemy модели
  schemas/    — Pydantic схемы
  api/v1/     — роутеры: products, categories, leads, auth, redirects
  services/   — уведомления о заявках
alembic/      — миграции БД
scripts/      — скрипт импорта данных из старого WordPress
legacy_data/  — CSV с разобранным контентом старого сайта
docs/         — справочная SQL-схема, карта URL, список редиректов
```

## Безопасность

- Все секреты (SECRET_KEY, пароли БД) должны браться из переменных окружения.
- Административные эндпоинты защищены JWT + ролью (editor/admin).
