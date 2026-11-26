"""
app/models/pages.py
Модели контентных страниц сайта: типы страниц, страницы
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Text,
    Boolean,
    Integer,
    String,
    DateTime,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.media import ContentImage


class PageType(Base):
    __tablename__ = "page_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    cta_eyebrow: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cta_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cta_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cta_button: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cta_href: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    pages: Mapped[list["Page"]] = relationship(back_populates="page_type")

    def __repr__(self) -> str:
        return self.name


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    legacy_wp_id: Mapped[Optional[int]] = mapped_column(
        Integer, unique=True, nullable=True
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pages.id"), nullable=True
    )
    page_type_id: Mapped[int] = mapped_column(
        ForeignKey("page_types.id"), nullable=False
    )

    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=expression.true(),
        nullable=False,
        index=True,
    )
    noindex: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=expression.false(),
        nullable=False,
    )
    seo_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent: Mapped[Optional["Page"]] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Page"]] = relationship(back_populates="parent")
    page_type: Mapped["PageType"] = relationship(back_populates="pages")
    images: Mapped[list["ContentImage"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="ContentImage.sort_order",
    )
    documents: Mapped[list["PageDocument"]] = relationship(
        back_populates="page",
        cascade="all, delete-orphan",
        order_by="PageDocument.sort_order",
    )

    related_links: Mapped[list["PageRelatedLink"]] = relationship(
        back_populates="page",
        foreign_keys="PageRelatedLink.page_id",
        cascade="all, delete-orphan",
        order_by="PageRelatedLink.sort_order, PageRelatedLink.id",
    )

    def __repr__(self) -> str:
        return self.title


class PageDocument(Base):
    __tablename__ = "page_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    page: Mapped["Page"] = relationship(back_populates="documents")


class PageRelatedLink(Base):
    """Связанный раздел: карточка «Читайте также» внизу страницы."""

    __tablename__ = "page_related_links"
    __table_args__ = (
        UniqueConstraint(
            "page_id", "related_page_id", name="uq_page_related_links_pair"
        ),
        CheckConstraint(
            "page_id <> related_page_id", name="ck_page_related_links_not_self"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    related_page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    card_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    page: Mapped["Page"] = relationship(
        back_populates="related_links", foreign_keys=[page_id]
    )
    related_page: Mapped["Page"] = relationship(foreign_keys=[related_page_id])

    def __repr__(self) -> str:
        return f"{self.page_id} → {self.related_page_id}"
