import asyncio
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/app/backups"))
BACKUP_KEEP = int(os.getenv("BACKUP_KEEP", "14"))
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+\.dump$")
_lock = asyncio.Lock()


def list_backups() -> list[dict]:
    if not BACKUP_DIR.exists():
        return []
    items = []
    for p in BACKUP_DIR.glob("*.dump"):
        st = p.stat()
        items.append({
            "name": p.name,
            "size_mb": round(st.st_size / 1024 / 1024, 2),
            "created": datetime.fromtimestamp(st.st_mtime, timezone.utc)
                       .strftime("%Y-%m-%d %H:%M UTC"),
            "mtime": st.st_mtime,
        })
    return sorted(items, key=lambda i: i["mtime"], reverse=True)


def resolve_backup(name: str) -> Path | None:
    if not NAME_RE.fullmatch(name):
        return None
    path = (BACKUP_DIR / name).resolve()
    if path.parent != BACKUP_DIR.resolve() or not path.is_file():
        return None
    return path


def _prune() -> None:
    for old in list_backups()[BACKUP_KEEP:]:
        (BACKUP_DIR / old["name"]).unlink(missing_ok=True)


async def create_backup() -> Path:
    if _lock.locked():
        raise RuntimeError("Бэкап уже создаётся, подождите.")
    async with _lock:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        final = BACKUP_DIR / f"{settings.POSTGRES_DB}_{stamp}.dump"
        part = final.with_name(final.name + ".part")

        proc = await asyncio.create_subprocess_exec(
            "pg_dump", "--format=custom", "--no-owner",
            "-h", settings.POSTGRES_HOST,
            "-p", str(settings.POSTGRES_PORT),
            "-U", settings.POSTGRES_USER,
            "-d", settings.POSTGRES_DB,
            "-f", str(part),
            env={**os.environ, "PGPASSWORD": settings.POSTGRES_PASSWORD},
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=900)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            part.unlink(missing_ok=True)
            raise RuntimeError("pg_dump не уложился в 15 минут.")

        if proc.returncode != 0:
            part.unlink(missing_ok=True)
            msg = stderr.decode(errors="replace").strip()[-300:]
            raise RuntimeError(f"pg_dump завершился с ошибкой: {msg}")

        part.replace(final)
        final.chmod(0o644)
        _prune()
        return final