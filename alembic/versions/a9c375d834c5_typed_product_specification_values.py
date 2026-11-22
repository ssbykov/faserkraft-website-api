"""typed product specification values

Revision ID: a9c375d834c5
Revises: 3ad0fa08a4aa
Create Date: 2026-11-22 19:31:11.361873

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a9c375d834c5"
down_revision: Union[str, None] = "3ad0fa08a4aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_specifications",
        sa.Column(
            "value_type",
            sa.String(length=20),
            nullable=False,
            server_default="text",
        ),
    )

    op.add_column(
        "product_specifications",
        sa.Column(
            "asset_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_product_specifications_asset_id",
        "product_specifications",
        "media_assets",
        ["asset_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_product_specifications_asset_id",
        "product_specifications",
        ["asset_id"],
        unique=False,
    )

    op.create_check_constraint(
        "ck_product_specifications_value_type",
        "product_specifications",
        "value_type IN ('text', 'image')",
    )

    op.create_check_constraint(
        "ck_product_specifications_value_shape",
        "product_specifications",
        "(value_type = 'text' AND asset_id IS NULL) OR "
        "(value_type = 'image' AND asset_id IS NOT NULL "
        "AND value IS NOT NULL AND length(trim(value)) > 0)",
    )


def downgrade() -> None:
    connection = op.get_bind()

    image_count = connection.execute(
        sa.text(
            "SELECT count(*) "
            "FROM product_specifications "
            "WHERE value_type <> 'text' "
            "OR asset_id IS NOT NULL"
        )
    ).scalar_one()

    if image_count:
        raise RuntimeError(
            "Откат отменён: существуют характеристики "
            "с изображениями. Сначала сохраните и явно "
            "преобразуйте их привязки."
        )

    op.drop_constraint(
        "ck_product_specifications_value_shape",
        "product_specifications",
        type_="check",
    )

    op.drop_constraint(
        "ck_product_specifications_value_type",
        "product_specifications",
        type_="check",
    )

    op.drop_index(
        "ix_product_specifications_asset_id",
        table_name="product_specifications",
    )

    op.drop_constraint(
        "fk_product_specifications_asset_id",
        "product_specifications",
        type_="foreignkey",
    )

    op.drop_column("product_specifications", "asset_id")
    op.drop_column("product_specifications", "value_type")
