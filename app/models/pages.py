"""
app/models/pages.py
Модели контентных страниц сайта: типы страниц, страницы, изображения страниц
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Text, Boolean, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PageType(Base):
    __tablename__ = "page_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    pages: Mapped[list["Page"]] = relationship(back_populates="page_type")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    legacy_wp_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pages.id"), nullable=True)
    page_type_id: Mapped[int] = mapped_column(ForeignKey("page_types.id"), nullable=False)

    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="published")
    seo_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent: Mapped[Optional["Page"]] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Page"]] = relationship(back_populates="parent")
    page_type: Mapped["PageType"] = relationship(back_populates="pages")
    images: Mapped[list["PageImage"]] = relationship(
        back_populates="page", cascade="all, delete-orphan", order_by="PageImage.sort_order"
    )


class PageImage(Base):
    __tablename__ = "page_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    page: Mapped["Page"] = relationship(back_populates="images")
