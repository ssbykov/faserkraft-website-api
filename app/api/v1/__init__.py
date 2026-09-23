"""
app/api/v1/__init__.py
Сборка маршрутов API v1.
"""
from fastapi import APIRouter

from app.api.v1 import auth, categories, leads, pages, products, redirects, menus

router = APIRouter()

router.include_router(auth.router)
router.include_router(categories.router)
router.include_router(products.router)
router.include_router(pages.router)
router.include_router(leads.router)
router.include_router(redirects.router)
router.include_router(menus.router)