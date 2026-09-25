"""
app/models/homepage.py
Модели управляемой главной страницы сайта Faserkraft.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models import Page, Product

class HomepageSection(Base):
    __tablename__ = "homepage_sections"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    eyebrow: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    button_label: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    button_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )
    secondary_button_label: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    secondary_button_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    cards: Mapped[list["HomepageCard"]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="HomepageCard.sort_order",
    )

    def __repr__(self) -> str:
        return self.code

class HomepageCard(Base):
    __tablename__ = "homepage_cards"

    id: Mapped[int] = mapped_column(primary_key=True)

    section_id: Mapped[int] = mapped_column(
        ForeignKey("homepage_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title_override: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    description_override: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    button_label: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    button_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    section: Mapped["HomepageSection"] = relationship(back_populates="cards")

    page: Mapped[Optional[Page]] = relationship(
        foreign_keys=[page_id],
    )
    product: Mapped[Optional[Product]] = relationship(
        foreign_keys=[product_id],
    )

    def __repr__(self) -> str:
        title = self.title_override or self.label
        return (
            f"<HomepageCard id={self.id} "
            f"section_id={self.section_id} "
            f"title={title!r} "
            f"visible={self.is_visible}>"
        )
