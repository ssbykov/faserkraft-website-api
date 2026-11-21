"""add company_info

Revision ID: 3fc63b2631da
Revises: 6e6c3b378d34
Create Date: 2026-11-21 15:17:52.457166

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "3fc63b2631da"
down_revision: Union[str, None] = "6e6c3b378d34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("short_name", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=500), nullable=True),
        sa.Column("inn", sa.String(length=12), nullable=True),
        sa.Column("kpp", sa.String(length=9), nullable=True),
        sa.Column("ogrn", sa.String(length=15), nullable=True),
        sa.Column("legal_address", sa.String(length=500), nullable=True),
        sa.Column("actual_address", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("bank_name", sa.String(length=255), nullable=True),
        sa.Column("bik", sa.String(length=9), nullable=True),
        sa.Column("settlement_account", sa.String(length=20), nullable=True),
        sa.Column("correspondent_account", sa.String(length=20), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("company_info")
