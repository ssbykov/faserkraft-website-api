"""
app/core/config.py
Конфигурация приложения через переменные окружения (.env)
"""
import secrets
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WEAK_SECRETS = {"", "changeme", "changeme-super-secret-key", "secret"}
WEAK_DB_PASSWORDS = {"", "changeme", "postgres", "password"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Faserkraft Website API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "faserkraft"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "faserkraft"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    ADMIN_SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 8

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # True только если API стоит за вашим прокси и он сам выставляет X-Forwarded-For
    TRUST_PROXY: bool = False

    FRONTEND_REVALIDATE_URL: str | None = None
    FRONTEND_REVALIDATE_SECRET: str | None = None

    S3_ENDPOINT_URL: str = "https://s3.example.com"
    S3_BUCKET: str = "faserkraft-media"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_PUBLIC_BASE_URL: str = "https://cdn.faserkraft.ru"

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _check_secrets(self) -> "Settings":
        weak_key = self.SECRET_KEY in WEAK_SECRETS or len(self.SECRET_KEY) < 32
        if self.IS_PRODUCTION:
            if weak_key:
                raise ValueError(
                    "SECRET_KEY пустой или слабый (нужно минимум 32 символа). Сгенерируйте: "
                    'python -c "import secrets; print(secrets.token_urlsafe(48))"'
                )
            if self.POSTGRES_PASSWORD in WEAK_DB_PASSWORDS:
                raise ValueError("POSTGRES_PASSWORD пустой или слабый для production.")
            if any(o.startswith("http://localhost") or o.startswith("http://127.") for o in self.CORS_ORIGINS):
                raise ValueError("CORS_ORIGINS в production не должен содержать localhost.")
        elif weak_key:
            # dev: случайный ключ на время жизни процесса (сессии админки сбросятся при перезапуске)
            self.SECRET_KEY = secrets.token_urlsafe(48)
        return self

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
