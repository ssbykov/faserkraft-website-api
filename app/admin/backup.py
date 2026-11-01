import logging
import time

from sqladmin import BaseView, expose
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)

from app.admin.auth import SESSION_ROLE_KEY, SESSION_USER_KEY
from app.db.session import AsyncSessionLocal
from app.models import User
from app.services import backup as backup_service
from app.services.restore import restore_state, start_restore
from app.services.yandex_disk import YaDisk


async def _is_admin(request: Request) -> bool:
    email = request.session.get(SESSION_USER_KEY)
    if not email:
        return False
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
    return bool(user and user.is_active and user.role == "admin")


class BackupAdmin(BaseView):
    name = "Резервные копии"
    icon = "fa-solid fa-database"
    identity = "backups"

    def is_accessible(self, request: Request) -> bool:
        return request.session.get(SESSION_ROLE_KEY) == "admin"

    @expose("/backups", methods=["GET", "POST"])
    async def backups_page(self, request: Request):
        if not await _is_admin(request):
            return PlainTextResponse("Доступ запрещён", status_code=403)

        base = request.url.path.rstrip("/")

        if request.method == "POST":
            try:
                path = await backup_service.create_backup()
                request.session["backup_flash"] = {
                    "ok": True,
                    "text": f"Бэкап создан: {path.name}",
                }
            except Exception as exc:
                logging.exception("Ошибка создания бэкапа")
                request.session["backup_flash"] = {
                    "ok": False,
                    "text": f"{type(exc).__name__}: {exc}",
                }
            return RedirectResponse(base, status_code=303)

        remote_backups, remote_error = [], None
        try:
            remote_backups = await YaDisk().list_backups()
        except Exception as exc:
            logging.exception("Не удалось получить список бэкапов с Яндекс Диска")
            remote_error = f"{type(exc).__name__}: {exc}"

        return await self.templates.TemplateResponse(
            request,
            "backups.html",
            {
                "backups": backup_service.list_backups(),
                "remote_backups": remote_backups,
                "remote_error": remote_error,
                "flash": request.session.pop("backup_flash", None),
                "download_url": f"{base}/download",
                "restore_url": f"{base}/restore",
                "status_url": f"{base}/status",
            },
        )

    @expose("/backups/download", methods=["GET"])
    async def download(self, request: Request):
        if not await _is_admin(request):
            return PlainTextResponse("Доступ запрещён", status_code=403)

        path = backup_service.resolve_backup(request.query_params.get("name", ""))
        if path is None:
            return PlainTextResponse("Файл не найден", status_code=404)

        return FileResponse(
            path,
            media_type="application/octet-stream",
            filename=path.name,
        )

    @expose("/backups/restore", methods=["POST"])
    async def restore(self, request: Request):
        if not await _is_admin(request):
            return PlainTextResponse("Доступ запрещён", status_code=403)

        base = request.url.path.rstrip("/").rsplit("/restore", 1)[0]
        form = await request.form()
        name = str(form.get("name", ""))
        confirm = str(form.get("confirm", "")).strip()

        if not name or confirm != name:
            request.session["backup_flash"] = {
                "ok": False,
                "text": "Подтверждение не совпало с именем файла, восстановление отменено.",
            }
            return RedirectResponse(base, status_code=303)

        try:
            start_restore(name)
        except RuntimeError as exc:
            request.session["backup_flash"] = {"ok": False, "text": str(exc)}
        return RedirectResponse(base, status_code=303)

    @expose("/backups/status", methods=["GET"])
    async def status(self, request: Request):
        if not await _is_admin(request):
            return JSONResponse({"error": "forbidden"}, status_code=403)

        data = dict(restore_state)
        finished_at = data.pop("finished_at", None)
        data["age"] = None if finished_at is None else time.time() - finished_at
        return JSONResponse(data)
