"""
app/services/media_sync.py
Синхронизация media/images с папкой на Яндекс Диске.

Только добавляет недостающие файлы: ничего не удаляет и не перезаписывает.
Совпавшие имена с разным размером считаются конфликтом и пропускаются.
"""

import asyncio
import logging
import re
import time
from pathlib import Path

from app.core.config import settings
from app.services.media import IMAGES_SUBDIR, MEDIA_DIR, MediaValidationError, prepare_image
from app.services.yandex_disk import YaDisk

IMAGES_DIR = MEDIA_DIR / IMAGES_SUBDIR
FILE_RE = re.compile(
    r"^(?!\.)[A-Za-z0-9_.-]+\.(?:jpg|jpeg|png|webp|svg)$", re.IGNORECASE
)
DIRECTIONS = ("push", "pull", "both")
CONCURRENCY = 4

_lock = asyncio.Lock()
_task: asyncio.Task | None = None

sync_state: dict = {
    "running": False,
    "direction": "",
    "stage": "",
    "percent": 0,
    "ok": None,
    "message": "",
    "finished_at": None,
}


def _disk() -> YaDisk:
    return YaDisk(settings.YANDEX_DISK_MEDIA_FOLDER)


def _local_files() -> dict[str, int]:
    if not IMAGES_DIR.exists():
        return {}
    return {
        p.name: p.stat().st_size
        for p in IMAGES_DIR.iterdir()
        if p.is_file() and FILE_RE.fullmatch(p.name)
    }


async def build_plan() -> dict:
    remote_all = await _disk().list_files()
    remote = {n: s for n, s in remote_all.items() if FILE_RE.fullmatch(n)}
    local = await asyncio.to_thread(_local_files)

    common = local.keys() & remote.keys()
    conflicts = sorted(n for n in common if local[n] != remote[n])
    return {
        "local_total": len(local),
        "remote_total": len(remote),
        "to_upload": sorted(local.keys() - remote.keys()),
        "to_download": sorted(remote.keys() - local.keys()),
        "conflicts": conflicts,
        "same": len(common) - len(conflicts),
    }


async def _run_many(names: list[str], action, base: int, span: int) -> list[str]:
    """Выполняет action(name) параллельно; возвращает список ошибок."""
    if not names:
        return []
    semaphore = asyncio.Semaphore(CONCURRENCY)
    errors: list[str] = []
    done = 0

    async def one(name: str) -> None:
        nonlocal done
        async with semaphore:
            try:
                await action(name)
            except Exception as exc:
                logging.exception("Ошибка синхронизации файла %s", name)
                errors.append(f"{name}: {exc}")
            done += 1
            sync_state["percent"] = base + int(span * done / len(names))

    await asyncio.gather(*(one(n) for n in names))
    return errors


async def _download_one(disk: YaDisk, name: str) -> None:
    part = IMAGES_DIR / f"{name}.part"
    final = IMAGES_DIR / name
    try:
        await disk.download_file(name, part)
        content = await asyncio.to_thread(part.read_bytes)
        try:
            _, safe_content = prepare_image(content)
        except MediaValidationError as exc:
            raise RuntimeError(f"файл не прошёл проверку: {exc}") from exc
        await asyncio.to_thread(final.write_bytes, safe_content)
    finally:
        part.unlink(missing_ok=True)


async def _sync(direction: str) -> str:
    async with _lock:
        disk = _disk()
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        sync_state.update(stage="Сравнение файлов", percent=5)
        plan = await build_plan()
        errors: list[str] = []
        uploaded = downloaded = 0

        if direction in ("push", "both") and plan["to_upload"]:
            sync_state.update(stage="Выгрузка на Яндекс Диск")
            await disk.ensure_folder()
            errors += await _run_many(
                plan["to_upload"],
                lambda n: disk.upload_file(IMAGES_DIR / n),
                base=10,
                span=40,
            )
            uploaded = len(plan["to_upload"])

        if direction in ("pull", "both") and plan["to_download"]:
            sync_state.update(stage="Загрузка с Яндекс Диска")
            errors += await _run_many(
                plan["to_download"],
                lambda n: _download_one(disk, n),
                base=50,
                span=48,
            )
            downloaded = len(plan["to_download"])

        message = (
            f"Выгружено файлов: {uploaded}, загружено: {downloaded}, "
            f"конфликтов (пропущено): {len(plan['conflicts'])}."
        )
        if errors:
            raise RuntimeError(message + f" Ошибок: {len(errors)}. Первая: {errors[0]}")
        return message


async def _run(direction: str) -> None:
    try:
        message = await _sync(direction)
        sync_state.update(ok=True, stage="Готово", percent=100, message=message)
    except Exception as exc:
        logging.exception("Ошибка синхронизации медиафайлов")
        sync_state.update(ok=False, stage="Ошибка", message=f"{type(exc).__name__}: {exc}")
    finally:
        sync_state.update(running=False, finished_at=time.time())


def start_sync(direction: str) -> None:
    global _task
    if direction not in DIRECTIONS:
        raise RuntimeError("Неизвестное направление синхронизации.")
    if sync_state["running"]:
        raise RuntimeError("Синхронизация уже выполняется.")
    sync_state.update(
        running=True, direction=direction, stage="Запуск", percent=0,
        ok=None, message="", finished_at=None,
    )
    _task = asyncio.create_task(_run(direction))