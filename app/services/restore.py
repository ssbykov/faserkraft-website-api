import asyncio
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from app.core.config import settings
from app.db.session import engine
from app.services.backup import BACKUP_DIR, NAME_RE, create_backup
from app.services.yandex_disk import YaDisk

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_restore_lock = asyncio.Lock()
_task: asyncio.Task | None = None

restore_state: dict = {
    "running": False,
    "stage": "",
    "percent": 0,
    "ok": None,
    "message": "",
    "name": "",
    "finished_at": None,
}


def _set(stage: str, percent: int) -> None:
    restore_state.update(stage=stage, percent=percent)


def _pg_env() -> dict:
    return {**os.environ, "PGPASSWORD": settings.POSTGRES_PASSWORD}


def _pg_conn_args() -> list[str]:
    return [
        "-h", str(settings.POSTGRES_HOST),
        "-p", str(settings.POSTGRES_PORT),
        "-U", settings.POSTGRES_USER,
    ]


def _fail(prefix: str, result: subprocess.CompletedProcess) -> None:
    msg = result.stderr.decode(errors="replace").strip()[-400:]
    raise RuntimeError(f"{prefix}: {msg}")


def _check_archive(path: Path) -> None:
    try:
        result = subprocess.run(
            ["pg_restore", "--list", str(path)],
            capture_output=True,
            timeout=120,
        )
    except FileNotFoundError:
        raise RuntimeError("pg_restore не найден: установите PostgreSQL client.")
    if result.returncode != 0:
        _fail("Файл не похож на корректный дамп PostgreSQL", result)


def _run_pg_restore(path: Path) -> None:
    result = subprocess.run(
        [
            "pg_restore",
            "--clean", "--if-exists",
            "--single-transaction",
            "--no-owner",
            *_pg_conn_args(),
            "-d", settings.POSTGRES_DB,
            str(path),
        ],
        env=_pg_env(),
        capture_output=True,
        timeout=1800,
    )
    if result.returncode != 0:
        _fail("pg_restore завершился с ошибкой (база не изменена)", result)


def _run_migrations() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        timeout=600,
    )
    if result.returncode != 0:
        _fail("База восстановлена, но миграции не применились", result)


async def _restore(remote_name: str) -> str:
    async with _restore_lock:
        disk = YaDisk()
        available = {item["name"] for item in await disk.list_backups()}
        if remote_name not in available:
            raise RuntimeError("Такого файла нет на Яндекс Диске.")

        tmp = BACKUP_DIR / "_restore" / remote_name
        try:
            _set("Скачивание с Яндекс Диска", 10)
            await disk.download_backup(remote_name, tmp)

            _set("Проверка архива", 25)
            await asyncio.to_thread(_check_archive, tmp)

            _set("Страховочный бэкап текущей базы", 50)
            safety = await create_backup()

            _set("Восстановление базы", 80)
            await asyncio.to_thread(_run_pg_restore, tmp)
            await engine.dispose()

            _set("Применение миграций", 95)
            await asyncio.to_thread(_run_migrations)
            await engine.dispose()
            return safety.name
        finally:
            tmp.unlink(missing_ok=True)


async def _run(remote_name: str) -> None:
    try:
        safety_name = await _restore(remote_name)
        restore_state.update(
            ok=True,
            stage="Готово",
            percent=100,
            message=f"База восстановлена из {remote_name}. "
                    f"Страховочная копия прежней базы: {safety_name}.",
        )
    except Exception as exc:
        logging.exception("Ошибка восстановления из бэкапа")
        restore_state.update(
            ok=False,
            stage="Ошибка",
            message=f"{type(exc).__name__}: {exc}",
        )
    finally:
        restore_state.update(running=False, finished_at=time.time())


def start_restore(remote_name: str) -> None:
    global _task
    if not NAME_RE.fullmatch(remote_name):
        raise RuntimeError("Некорректное имя файла.")
    if restore_state["running"]:
        raise RuntimeError("Восстановление уже выполняется.")

    restore_state.update(
        running=True,
        stage="Запуск",
        percent=0,
        ok=None,
        message="",
        name=remote_name,
        finished_at=None,
    )
    _task = asyncio.create_task(_run(remote_name))