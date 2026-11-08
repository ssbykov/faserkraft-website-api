"""
app/models/catalog.py
Модели каталога продукции: категории, товары, характеристики, изображения, документы
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Text,
    Boolean,
    Integer,
    String,
    DateTime,
    func,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.db.session import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    products: Mapped[list["Product"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return self.name


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    legacy_wp_id: Mapped[Optional[int]] = mapped_column(
        Integer, unique=True, nullable=True
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("product_categories.id"), nullable=True
    )
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    membrane_material: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=expression.true(),
        nullable=False,
        index=True,
    )
    seo_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category: Mapped[Optional["ProductCategory"]] = relationship(
        back_populates="products"
    )
    specifications: Mapped[list["ProductSpecification"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )
    documents: Mapped[list["ProductDocument"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductDocument.sort_order",
    )

    def __repr__(self) -> str:
        return self.name


class SpecificationGroup(Base):
    __tablename__ = "specification_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    parameters: Mapped[list["SpecificationParameter"]] = relationship(
        back_populates="group", order_by="SpecificationParameter.sort_order"
    )

    def __repr__(self) -> str:
        return self.name


class SpecificationParameter(Base):
    __tablename__ = "specification_parameters"
    __table_args__ = (UniqueConstraint("group_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("specification_groups.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    code: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    is_filterable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=expression.false(),
        nullable=False,
    )
    list_sort_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    group: Mapped["SpecificationGroup"] = relationship(
        back_populates="parameters",
        lazy="joined",
        innerjoin=True,
    )

    def __repr__(self) -> str:
        return self.name


class ProductCardField(Base):
    """Поле карточки товара в списке: ключ для фронтенда + параметр-источник."""

    __tablename__ = "product_card_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parameter_id: Mapped[int] = mapped_column(
        ForeignKey("specification_parameters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=expression.true(), nullable=False
    )

    parameter: Mapped["SpecificationParameter"] = relationship(
        lazy="joined", innerjoin=True
    )

    def __repr__(self) -> str:
        return self.key


class ProductSpecification(Base):
    __tablename__ = "product_specifications"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "parameter_id",
            name="uq_product_specifications_product_parameter",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    parameter_id: Mapped[int] = mapped_column(
        ForeignKey("specification_parameters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="specifications")
    parameter: Mapped["SpecificationParameter"] = relationship(
        lazy="joined",
        innerjoin=True,
    )

    # Плоский вид для текущего API и фронтенда
    @property
    def group_name(self) -> str:
        return self.parameter.group.name

    @property
    def parameter_name(self) -> str:
        return self.parameter.name

    @property
    def parameter_value(self) -> Optional[str]:
        return self.value

    @property
    def sort_order(self) -> int:
        return self.parameter.group.sort_order * 1000 + self.parameter.sort_order

    def __repr__(self) -> str:
        return self.parameter_name


PRODUCT_IMAGE_KINDS = ("cover", "gallery", "drawing")


class MediaAsset(Base):
    """Файл библиотеки: один файл можно привязать ко многим товарам."""

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    product_images: Mapped[list["ProductImage"]] = relationship(back_populates="asset")

    def __repr__(self) -> str:
        return self.title or self.file_url.rsplit("/", 1)[-1]


class ProductImage(Base):
    """Привязка файла к товару: назначение (kind) и порядок."""

    __tablename__ = "product_images"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('cover', 'gallery', 'drawing')",
            name="ck_product_images_kind",
        ),
        UniqueConstraint(
            "product_id", "asset_id", name="uq_product_images_product_asset"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
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

    product: Mapped["Product"] = relationship(back_populates="images")
    asset: Mapped["MediaAsset"] = relationship(
        back_populates="product_images", lazy="joined", innerjoin=True
    )

    @property
    def image_url(self) -> str:
        return self.asset.file_url

    @property
    def alt_text(self) -> Optional[str]:
        return self.asset.alt_text

    def __repr__(self) -> str:
        return self.asset.file_url if self.asset else f"ProductImage {self.id}"


class ProductDocument(Base):
    __tablename__ = "product_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=True
    )
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped[Optional["Product"]] = relationship(back_populates="documents")

    def __repr__(self) -> str:
        return self.document_type or "Документа нет"
