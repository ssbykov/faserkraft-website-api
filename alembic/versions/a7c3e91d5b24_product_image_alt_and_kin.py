"""product images: alt_text and kind

Revision ID: a7c3e91d5b24
Revises: 1321a5463f81
Create Date: 2026-11-07 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c3e91d5b24"
down_revision: Union[str, None] = "1321a5463f81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_images",
        sa.Column("alt_text", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "product_images",
        sa.Column(
            "kind",
            sa.String(length=20),
            server_default="gallery",
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_product_images_kind"), "product_images", ["kind"], unique=False
    )
    op.create_check_constraint(
        "ck_product_images_kind",
        "product_images",
        "kind IN ('cover', 'gallery', 'drawing')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_product_images_kind", "product_images", type_="check")
    op.drop_index(op.f("ix_product_images_kind"), table_name="product_images")
    op.drop_column("product_images", "kind")
    op.drop_column("product_images", "alt_text")
