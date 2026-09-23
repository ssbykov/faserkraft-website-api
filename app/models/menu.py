from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, func, CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models import Page, Product


class Menu(Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(
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

    items: Mapped[list["MenuItem"]] = relationship(
        back_populates="menu",
        cascade="all, delete-orphan",
        order_by="MenuItem.sort_order",
    )


class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint(
            """
            (
                CASE WHEN page_id IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN product_id IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN url IS NOT NULL AND url <> '' THEN 1 ELSE 0 END
            ) <= 1
            """,
            name="ck_menu_items_one_link_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    menu_id: Mapped[int] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"),
        nullable=True,
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
    url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    target_blank: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
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

    menu: Mapped["Menu"] = relationship(back_populates="items")

    parent: Mapped[Optional["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="children",
        remote_side="MenuItem.id",
        foreign_keys=[parent_id],
    )
    children: Mapped[list["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="parent",
        cascade="all, delete-orphan",
        single_parent=True,
        foreign_keys=[parent_id],
        order_by="MenuItem.sort_order",
    )

    page: Mapped[Optional[Page]] = relationship(
        foreign_keys=[page_id],
    )
    product: Mapped[Optional[Product]] = relationship(
        foreign_keys=[product_id],
    )
