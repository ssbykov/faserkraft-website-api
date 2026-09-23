"""add homepage content models

Revision ID: dc4bc921eeab
Revises: 3b58d518e814
Create Date: 2026-09-23 18:23:38.954861

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "dc4bc921eeab"
down_revision: Union[str, None] = "3b58d518e814"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "homepage_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("eyebrow", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("button_label", sa.String(length=255), nullable=True),
        sa.Column("button_url", sa.String(length=1000), nullable=True),
        sa.Column(
            "secondary_button_label",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "secondary_button_url",
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "is_visible",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_homepage_sections_code"),
        "homepage_sections",
        ["code"],
        unique=True,
    )

    op.create_table(
        "homepage_cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("title_override", sa.String(length=500), nullable=True),
        sa.Column("description_override", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("button_label", sa.String(length=255), nullable=True),
        sa.Column("button_url", sa.String(length=1000), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "is_visible",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            """
            (
                CASE WHEN page_id IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN product_id IS NOT NULL THEN 1 ELSE 0 END
            ) <= 1
            """,
            name="ck_homepage_cards_one_content_source",
        ),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["pages.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["homepage_sections.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_homepage_cards_page_id"),
        "homepage_cards",
        ["page_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_homepage_cards_product_id"),
        "homepage_cards",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_homepage_cards_section_id"),
        "homepage_cards",
        ["section_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_homepage_cards_section_id"),
        table_name="homepage_cards",
    )
    op.drop_index(
        op.f("ix_homepage_cards_product_id"),
        table_name="homepage_cards",
    )
    op.drop_index(
        op.f("ix_homepage_cards_page_id"),
        table_name="homepage_cards",
    )
    op.drop_table("homepage_cards")

    op.drop_index(
        op.f("ix_homepage_sections_code"),
        table_name="homepage_sections",
    )
    op.drop_table("homepage_sections")