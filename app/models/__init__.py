"""
app/models/__init__.py
Точка сборки всех моделей — импортируется Alembic (target_metadata) и остальным кодом.
"""

from app.models.catalog import (
    Product,
    ProductCategory,
    ProductDocument,
    ProductSpecification,
    SpecificationGroup,
    SpecificationParameter,
    ProductCardField,
)
from app.models.company import CompanyInfo
from app.models.homepage import HomepageCard, HomepageSection
from app.models.leads import LeadRequest
from app.models.media import MediaAsset, ContentImage
from app.models.menus import Menu, MenuItem
from app.models.pages import Page, PageDocument, PageType
from app.models.redirects import Redirect
from app.models.users import User
from app.models.yandex_token import YandexToken

__all__ = [
    "Product",
    "ProductCategory",
    "ProductDocument",
    "ContentImage",
    "MediaAsset",
    "ProductSpecification",
    "SpecificationGroup",
    "SpecificationParameter",
    "ProductCardField",
    "Page",
    "PageDocument",
    "PageType",
    "User",
    "LeadRequest",
    "Redirect",
    "Menu",
    "MenuItem",
    "HomepageCard",
    "HomepageSection",
    "YandexToken",
    "CompanyInfo",
]
