"""
app/services/media_sync.py
Синхронизация media/images с папкой на Яндекс Диске.

Только добавляет недостающие файлы: ничего не удаляет и не перезаписывает.
Совпавшие имена с разным размером считаются конфликтом и пропускаются.
"""

import asyncio
import hashlib
import logging
import re
import time
from pathlib import Path

from app.core.config import settings
from app.services.media import (
    DOCUMENTS_SUBDIR,
    IMAGES_SUBDIR,
    MAX_PDF_BYTES,
    MEDIA_DIR,
    MediaValidationError,
    prepare_image,
)
from app.services.yandex_disk import YaDisk

IMAGES_DIR = MEDIA_DIR / IMAGES_SUBDIR
FILE_RE = re.compile(
    r"^(?!\.)[A-Za-z0-9_.-]+\.(?:jpg|jpeg|png|webp|svg)$", re.IGNORECASE
)
DOCUMENTS_DIR = MEDIA_DIR / DOCUMENTS_SUBDIR

PDF_FILE_RE = re.compile(
    r"^(?!\.)[A-Za-z0-9_.-]+\.pdf$",
    re.IGNORECASE,
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

def _scopes():
    folder = settings.YANDEX_DISK_MEDIA_FOLDER.rstrip("/")

    return [
        (
            "images",
            IMAGES_DIR,
            YaDisk(folder),
            FILE_RE,
        ),
        (
            "documents",
            DOCUMENTS_DIR,
            YaDisk(f"{folder}/documents"),
            PDF_FILE_RE,
        ),
    ]

def _disk() -> YaDisk:
    return YaDisk(settings.YANDEX_DISK_MEDIA_FOLDER)


def _local_files(directory: Path, pattern: re.Pattern) -> dict[str, int]:
    if not directory.exists():
        return {}

    return {
        path.name: path.stat().st_size
        for path in directory.iterdir()
        if path.is_file() and pattern.fullmatch(path.name)
    }


async def _build_scope_plan(
    directory: Path,
    disk: YaDisk,
    pattern: re.Pattern,
) -> dict:
    remote_all = await disk.list_files()

    remote = {
        name: size
        for name, size in remote_all.items()
        if pattern.fullmatch(name)
    }

    local = await asyncio.to_thread(_local_files, directory, pattern)

    common = local.keys() & remote.keys()
    conflicts = sorted(name for name in common if local[name] != remote[name])

    return {
        "local_total": len(local),
        "remote_total": len(remote),
        "to_upload": sorted(local.keys() - remote.keys()),
        "to_download": sorted(remote.keys() - local.keys()),
        "conflicts": conflicts,
        "same": len(common) - len(conflicts),
    }


async def build_plan() -> dict:
    result = {
        "local_total": 0,
        "remote_total": 0,
        "to_upload": [],
        "to_download": [],
        "conflicts": [],
        "same": 0,
    }

    for label, directory, disk, pattern in _scopes():
        plan = await _build_scope_plan(directory, disk, pattern)

        for key in ("local_total", "remote_total", "same"):
            result[key] += plan[key]

        for key in ("to_upload", "to_download", "conflicts"):
            result[key].extend(
                f"{label}/{name}"
                for name in plan[key]
            )

    return result

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


async def _download_one(
    disk: YaDisk,
    name: str,
    directory: Path,
    is_pdf: bool,
) -> None:
    part = directory / f"{name}.part"
    final = directory / name

    def validate_and_publish() -> None:
        if is_pdf and part.stat().st_size > MAX_PDF_BYTES:
            raise RuntimeError("PDF превышает допустимый размер 20 МБ.")

        content = part.read_bytes()

        if is_pdf:
            if not content.startswith(b"%PDF-"):
                raise RuntimeError("Файл не является PDF.")

            stem = Path(name).stem

            if re.fullmatch(r"[0-9a-fA-F]{64}", stem):
                digest = hashlib.sha256(content).hexdigest()

                if digest != stem.lower():
                    raise RuntimeError(
                        "SHA-256 содержимого не совпадает с именем PDF."
                    )
        else:
            try:
                _, safe_content = prepare_image(content)
            except MediaValidationError as exc:
                raise RuntimeError(
                    f"Файл не прошёл проверку: {exc}"
                ) from exc

            part.write_bytes(safe_content)

        part.replace(final)

    try:
        await disk.download_file(name, part)
        await asyncio.to_thread(validate_and_publish)
    finally:
        await asyncio.to_thread(part.unlink, missing_ok=True)


async def _sync(direction: str) -> str:
    async with _lock:
        errors: list[str] = []
        uploaded = 0
        downloaded = 0
        conflicts = 0

        scopes = _scopes()
        scope_span = 100 // len(scopes)

        for index, (label, directory, disk, pattern) in enumerate(scopes):
            await asyncio.to_thread(
                directory.mkdir,
                parents=True,
                exist_ok=True,
            )

            base = index * scope_span

            sync_state.update(
                stage=f"{label}: сравнение файлов",
                percent=base,
            )

            plan = await _build_scope_plan(directory, disk, pattern)
            conflicts += len(plan["conflicts"])

            if direction in ("push", "both") and plan["to_upload"]:
                sync_state.update(
                    stage=f"{label}: выгрузка на Яндекс Диск"
                )

                await disk.ensure_folder()

                upload_errors = await _run_many(
                    plan["to_upload"],
                    lambda name: disk.upload_file(directory / name),
                    base=base + 5,
                    span=20,
                )

                uploaded += len(plan["to_upload"]) - len(upload_errors)

                errors.extend(
                    f"{label}/{error}"
                    for error in upload_errors
                )

            if direction in ("pull", "both") and plan["to_download"]:
                sync_state.update(
                    stage=f"{label}: загрузка с Яндекс Диска"
                )

                download_errors = await _run_many(
                    plan["to_download"],
                    lambda name: _download_one(
                        disk,
                        name,
                        directory,
                        is_pdf=(label == "documents"),
                    ),
                    base=base + 25,
                    span=24,
                )

                downloaded += len(plan["to_download"]) - len(download_errors)

                errors.extend(
                    f"{label}/{error}"
                    for error in download_errors
                )

        message = (
            f"Выгружено файлов: {uploaded}, "
            f"загружено: {downloaded}, "
            f"конфликтов (пропущено): {conflicts}."
        )

        if errors:
            raise RuntimeError(
                message
                + f" Ошибок: {len(errors)}. Первая: {errors[0]}"
            )

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