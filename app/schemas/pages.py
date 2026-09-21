"""
app/schemas/pages.py
Pydantic v2 схемы контентных страниц.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PageTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    template: Optional[str] = None


class PageImageBase(BaseModel):
    image_url: str
    alt_text: Optional[str] = None
    is_cover: bool = False
    sort_order: int = 0


class PageImageOut(PageImageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class PageBase(BaseModel):
    slug: str
    title: str
    content: Optional[str] = None
    status: str = "published"
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    sort_order: int = 0


class PageCreate(PageBase):
    legacy_wp_id: Optional[int] = None
    parent_id: Optional[int] = None
    page_type_id: int


class PageUpdate(BaseModel):
    parent_id: Optional[int] = None
    page_type_id: Optional[int] = None
    slug: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    sort_order: Optional[int] = None


class PageListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    status: str
    sort_order: int
    parent_id: Optional[int] = None
    page_type: PageTypeOut


class PageOut(PageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    page_type: PageTypeOut
    images: list[PageImageOut] = Field(default_factory=list)
    children: list[PageListItem] = Field(default_factory=list)