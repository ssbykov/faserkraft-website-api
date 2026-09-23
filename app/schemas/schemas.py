"""
app/schemas/schemas.py

Совместимый фасад для Pydantic-схем.

Схемы декомпозированы по доменам в app/schemas/*.py. Этот файл намеренно
оставлен, чтобы ранее существовавшие импорты вида
`from app.schemas.schemas import ProductOut` продолжали работать.

Новый код предпочтительно импортирует схемы из профильных модулей, например:
`from app.schemas.products import ProductOut`.
"""
from app.schemas.auth import Token, UserOut
from app.schemas.leads import LeadRequestCreate, LeadRequestOut
from app.schemas.pages import (
    PageBase,
    PageCreate,
    PageImageBase,
    PageImageOut,
    PageListItem,
    PageOut,
    PageTreeItem,
    PageTypeOut,
    PageUpdate,
    PageDocumentBase,
    PageDocumentOut,
)
from app.schemas.products import (
    ProductBase,
    ProductCategoryBase,
    ProductCategoryCreate,
    ProductCategoryOut,
    ProductCreate,
    ProductDocumentBase,
    ProductDocumentOut,
    ProductImageBase,
    ProductImageOut,
    ProductListItem,
    ProductOut,
    ProductSpecificationBase,
    ProductSpecificationCreate,
    ProductSpecificationOut,
    ProductUpdate,
)
from app.schemas.redirects import RedirectOut
from app.schemas.menus import MenuItemTreeOut, MenuTreeOut
from app.schemas.homepage import HomepageCardOut, HomepageSectionOut, HomepageOut

__all__ = [
    "ProductCategoryBase",
    "ProductCategoryCreate",
    "ProductCategoryOut",
    "ProductSpecificationBase",
    "ProductSpecificationCreate",
    "ProductSpecificationOut",
    "ProductImageBase",
    "ProductImageOut",
    "ProductDocumentBase",
    "ProductDocumentOut",
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductListItem",
    "ProductOut",
    "LeadRequestCreate",
    "LeadRequestOut",
    "Token",
    "UserOut",
    "RedirectOut",
    "PageBase",
    "PageCreate",
    "PageUpdate",
    "PageListItem",
    "PageTreeItem",
    "PageOut",
    "PageTypeOut",
    "PageImageBase",
    "PageImageOut",
    "PageDocumentBase",
    "PageDocumentOut",
    "MenuItemTreeOut",
    "MenuTreeOut",
    "HomepageCardOut",
    "HomepageSectionOut",
    "HomepageOut",
]
