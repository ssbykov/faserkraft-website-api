"""
app/main.py
Точка входа FastAPI-приложения бэкенда корпоративного сайта Faserkraft
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import setup_admin
from app.api.v1 import auth, categories, leads, products, redirects
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(leads.router, prefix=settings.API_V1_PREFIX)
app.include_router(redirects.router, prefix=settings.API_V1_PREFIX)

setup_admin(app)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}
