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
from app.models.pages import Page, PageImage, PageType
from app.models.users import User
from app.models.leads import LeadRequest
from app.models.redirects import Redirect

__all__ = [
    "Product",
    "ProductCategory",
    "ProductDocument",
    "ProductImage",
    "ProductSpecification",
    "Page",
    "PageImage",
    "PageType",
    "User",
    "LeadRequest",
    "Redirect",
]
