"""
app/main.py
Точка входа FastAPI-приложения бэкенда корпоративного сайта Faserkraft
"""
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.admin import setup_admin
from app.api.v1 import router as api_v1_router
from app.core.config import settings

MAX_BODY_BYTES = 1_000_000  # 1 МБ на запросы к /api

docs_enabled = not settings.IS_PRODUCTION

app = FastAPI(
    title="Faserkraft Website API",
    version="1.0.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path.startswith("/api"):
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "Слишком большой запрос"}, status_code=413)

    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if settings.IS_PRODUCTION:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.url.path.startswith(("/admin", "/api")):
        response.headers.setdefault("Cache-Control", "no-store") if request.url.path.startswith("/admin") else None
    return response


app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

setup_admin(app)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=not settings.IS_PRODUCTION,
    )
