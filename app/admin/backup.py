from sqladmin import BaseView, expose
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import FileResponse, PlainTextResponse, RedirectResponse

from app.admin.auth import SESSION_ROLE_KEY, SESSION_USER_KEY
from app.db.session import AsyncSessionLocal
from app.models import User
from app.services import backup as backup_service


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
                request.session["backup_flash"] = {"ok": False, "text": str(exc)}
            return RedirectResponse(base, status_code=303)

        return await self.templates.TemplateResponse(
            request,
            "backups.html",
            {
                "backups": backup_service.list_backups(),
                "flash": request.session.pop("backup_flash", None),
                "download_url": f"{base}/download",
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