"""
app/models/__init__.py
Точка сборки всех моделей — импортируется Alembic (target_metadata) и остальным кодом.
"""
from app.models.catalog import (
    Product,
    ProductCategory,
    ProductDocument,
    ProductImage,
    ProductSpecification,
)
from app.models.leads import LeadRequest
from app.models.pages import Page, PageDocument, PageImage, PageType
from app.models.redirects import Redirect
from app.models.users import User
from app.models.menus import Menu, MenuItem

__all__ = [
    "Product",
    "ProductCategory",
    "ProductDocument",
    "ProductImage",
    "ProductSpecification",
    "Page",
    "PageImage",
    "PageDocument",
    "PageType",
    "User",
    "LeadRequest",
    "Redirect",
    "Menu",
    "MenuItem",
]
