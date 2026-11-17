import logging
import time

from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse

from app.admin.auth import SESSION_ROLE_KEY
from app.admin.backup import _is_admin
from app.services.media_sync import build_plan, start_sync, sync_state


class MediaSyncAdmin(BaseView):
    name = "Синхронизация медиа"
    icon = "fa-solid fa-cloud-arrow-up"
    identity = "media-sync"

    def is_accessible(self, request: Request) -> bool:
        return request.session.get(SESSION_ROLE_KEY) == "admin"

    @expose("/media-sync", methods=["GET", "POST"])
    async def page(self, request: Request):
        if not await _is_admin(request):
            return PlainTextResponse("Доступ запрещён", status_code=403)

        base = request.url.path.rstrip("/")

        if request.method == "POST":
            form = await request.form()
            try:
                start_sync(str(form.get("direction", "")))
            except RuntimeError as exc:
                request.session["media_sync_flash"] = {"ok": False, "text": str(exc)}
            return RedirectResponse(base, status_code=303)

        plan, error = None, None
        try:
            plan = await build_plan()
        except Exception as exc:
            logging.exception("Не удалось сравнить медиафайлы с Яндекс Диском")
            error = f"{type(exc).__name__}: {exc}"

        return await self.templates.TemplateResponse(
            request,
            "media_sync.html",
            {
                "plan": plan,
                "error": error,
                "flash": request.session.pop("media_sync_flash", None),
                "status_url": f"{base}/status",
            },
        )

    @expose("/media-sync/status", methods=["GET"])
    async def status(self, request: Request):
        if not await _is_admin(request):
            return JSONResponse({"error": "forbidden"}, status_code=403)
        data = dict(sync_state)
        finished_at = data.pop("finished_at", None)
        data["age"] = None if finished_at is None else time.time() - finished_at
        return JSONResponse(data)

MEDIA_VIEWS = [MediaSyncAdmin]