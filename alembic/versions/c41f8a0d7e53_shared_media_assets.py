"""shared media assets for product images

Revision ID: c41f8a0d7e53
Revises: a7c3e91d5b24
Create Date: 2026-11-08 11:30:00.000000

Один файл - много товаров: файлы выносятся в media_assets, а product_images
становится связью "товар - файл" с назначением (kind) и порядком.
Перед применением сделайте резервную копию базы.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c41f8a0d7e53"
down_revision: Union[str, None] = "a7c3e91d5b24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("file_url", sa.String(length=1000), nullable=False),
        sa.Column("alt_text", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_url", name="uq_media_assets_file_url"),
    )

    # Каждый уникальный адрес из product_images становится файлом библиотеки
    op.execute("""
        INSERT INTO media_assets (title, file_url, alt_text)
        SELECT LEFT(REGEXP_REPLACE(image_url, '^.*/', ''), 255),
               image_url,
               MAX(alt_text)
        FROM product_images
        GROUP BY image_url
        """)

    op.add_column("product_images", sa.Column("asset_id", sa.Integer(), nullable=True))
    op.execute("""
        UPDATE product_images AS pi
        SET asset_id = ma.id
        FROM media_assets AS ma
        WHERE ma.file_url = pi.image_url
        """)
    op.alter_column("product_images", "asset_id", nullable=False)

    # Один и тот же файл дважды у одного товара не нужен
    op.execute("""
        DELETE FROM product_images AS a
        USING product_images AS b
        WHERE a.product_id = b.product_id
          AND a.asset_id = b.asset_id
          AND a.id > b.id
        """)

    op.create_foreign_key(
        "fk_product_images_asset_id",
        "product_images",
        "media_assets",
        ["asset_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_product_images_asset_id"), "product_images", ["asset_id"], unique=False
    )
    op.create_unique_constraint(
        "uq_product_images_product_asset", "product_images", ["product_id", "asset_id"]
    )

    op.drop_column("product_images", "image_url")
    op.drop_column("product_images", "alt_text")


def downgrade() -> None:
    op.add_column(
        "product_images",
        sa.Column("image_url", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "product_images",
        sa.Column("alt_text", sa.String(length=500), nullable=True),
    )
    op.execute("""
        UPDATE product_images AS pi
        SET image_url = ma.file_url,
            alt_text = ma.alt_text
        FROM media_assets AS ma
        WHERE ma.id = pi.asset_id
        """)
    op.alter_column("product_images", "image_url", nullable=False)

    op.drop_constraint(
        "uq_product_images_product_asset", "product_images", type_="unique"
    )
    op.drop_index(op.f("ix_product_images_asset_id"), table_name="product_images")
    op.drop_constraint(
        "fk_product_images_asset_id", "product_images", type_="foreignkey"
    )
    op.drop_column("product_images", "asset_id")
    op.drop_table("media_assets")
