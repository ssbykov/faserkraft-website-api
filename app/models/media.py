"""
app/models/media.py
Файлы библиотеки и их привязка к товарам и страницам
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.catalog import Product
    from app.models.pages import Page

CONTENT_IMAGE_KINDS = ("cover", "gallery", "drawing")


class MediaAsset(Base):
    """Файл библиотеки: один файл можно привязать ко многим товарам и страницам."""

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    content_images: Mapped[list["ContentImage"]] = relationship(back_populates="asset")

    def __repr__(self) -> str:
        return self.title or self.file_url.rsplit("/", 1)[-1]

    @property
    def shortcode(self) -> str:
        return "{{media:%d}}" % self.id


class ContentImage(Base):
    """Привязка файла к товару или странице: назначение (kind) и порядок."""

    __tablename__ = "content_images"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('cover', 'gallery', 'drawing')",
            name="ck_content_images_kind",
        ),
        CheckConstraint(
            "num_nonnulls(product_id, page_id) = 1",
            name="ck_content_images_one_owner",
        ),
        UniqueConstraint(
            "product_id", "asset_id", name="uq_content_images_product_asset"
        ),
        UniqueConstraint("page_id", "asset_id", name="uq_content_images_page_asset"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    page_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"), nullable=True, index=True
    )
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("media_assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(
        String(20),
        default="gallery",
        server_default="gallery",
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped[Optional["Product"]] = relationship(back_populates="images")
    page: Mapped[Optional["Page"]] = relationship(back_populates="images")
    asset: Mapped["MediaAsset"] = relationship(
        back_populates="content_images", lazy="joined", innerjoin=True
    )

    @property
    def image_url(self) -> str:
        return self.asset.file_url

    @property
    def alt_text(self) -> Optional[str]:
        return self.asset.alt_text

    @property
    def is_cover(self) -> bool:
        return self.kind == "cover"

    def __repr__(self) -> str:
        return self.asset.file_url if self.asset else f"ContentImage {self.id}"
