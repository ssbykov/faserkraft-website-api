"""unify product_images and page_images into content_images

Revision ID: 6e6c3b378d34
Revises: c41f8a0d7e53
Create Date: 2026-11-17 16:59:00.815658

Одна таблица привязок для товаров и страниц:
- product_images переименована в content_images, добавлен page_id,
  product_id стал nullable, CHECK требует ровно одного владельца;
- page_images перенесена в media_assets + content_images и удалена;
- пути /media/products/ заменены на /media/images/ в media_assets,
  pages.content, products.description и products.short_description.

Миграция необратима (downgrade не поддерживается).
Перед применением: бэкап базы и cp -a media/products/. media/images/
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "6e6c3b378d34"
down_revision: Union[str, None] = "c41f8a0d7e53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_PREFIX = "/media/products/"
NEW_PREFIX = "/media/images/"


def upgrade() -> None:
    # 1. Переименование таблицы и связанных объектов
    op.rename_table("product_images", "content_images")
    op.execute("ALTER INDEX product_images_pkey RENAME TO content_images_pkey")
    op.execute(
        "ALTER SEQUENCE IF EXISTS product_images_id_seq RENAME TO content_images_id_seq"
    )
    op.execute(
        "ALTER INDEX ix_product_images_asset_id RENAME TO ix_content_images_asset_id"
    )
    op.execute("ALTER INDEX ix_product_images_kind RENAME TO ix_content_images_kind")
    op.execute(
        "ALTER TABLE content_images "
        "RENAME CONSTRAINT ck_product_images_kind TO ck_content_images_kind"
    )
    op.execute(
        "ALTER TABLE content_images "
        "RENAME CONSTRAINT uq_product_images_product_asset "
        "TO uq_content_images_product_asset"
    )
    op.execute(
        "ALTER TABLE content_images "
        "RENAME CONSTRAINT fk_product_images_asset_id TO content_images_asset_id_fkey"
    )
    op.execute(
        "ALTER TABLE content_images "
        "RENAME CONSTRAINT product_images_product_id_fkey "
        "TO content_images_product_id_fkey"
    )

    # 2. Владелец: товар или страница
    op.alter_column(
        "content_images", "product_id", existing_type=sa.Integer(), nullable=True
    )
    op.add_column("content_images", sa.Column("page_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "content_images_page_id_fkey",
        "content_images",
        "pages",
        ["page_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_content_images_page_id"), "content_images", ["page_id"], unique=False
    )
    op.create_index(
        op.f("ix_content_images_product_id"),
        "content_images",
        ["product_id"],
        unique=False,
    )

    # 3. Картинки страниц -> библиотека + привязки
    op.execute(
        """
        INSERT INTO media_assets (title, file_url, alt_text)
        SELECT LEFT(REGEXP_REPLACE(image_url, '^.*/', ''), 255),
               image_url,
               MAX(alt_text)
        FROM page_images
        GROUP BY image_url
        ON CONFLICT (file_url) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO content_images (page_id, asset_id, kind, sort_order)
        SELECT DISTINCT ON (pi.page_id, ma.id)
               pi.page_id,
               ma.id,
               CASE WHEN pi.is_cover THEN 'cover' ELSE 'gallery' END,
               COALESCE(pi.sort_order, 0)
        FROM page_images AS pi
        JOIN media_assets AS ma ON ma.file_url = pi.image_url
        ORDER BY pi.page_id, ma.id, pi.is_cover DESC, pi.sort_order, pi.id
        """
    )
    op.drop_table("page_images")

    op.create_check_constraint(
        "ck_content_images_one_owner",
        "content_images",
        "num_nonnulls(product_id, page_id) = 1",
    )
    op.create_unique_constraint(
        "uq_content_images_page_asset", "content_images", ["page_id", "asset_id"]
    )

    # 4. Пути: /media/products/ -> /media/images/
    op.execute(
        sa.text(
            "UPDATE media_assets "
            "SET file_url = :new || SUBSTRING(file_url FROM :cut) "
            "WHERE file_url LIKE :pattern"
        ).bindparams(new=NEW_PREFIX, cut=len(OLD_PREFIX) + 1, pattern=OLD_PREFIX + "%")
    )
    for table, column in (
        ("pages", "content"),
        ("products", "description"),
        ("products", "short_description"),
    ):
        op.execute(
            sa.text(
                f"UPDATE {table} SET {column} = REPLACE({column}, :old, :new) "
                f"WHERE {column} LIKE :pattern"
            ).bindparams(old=OLD_PREFIX, new=NEW_PREFIX, pattern=f"%{OLD_PREFIX}%")
        )


def downgrade() -> None:
    raise NotImplementedError(
        "Миграция необратима: восстановите базу из резервной копии."
    )