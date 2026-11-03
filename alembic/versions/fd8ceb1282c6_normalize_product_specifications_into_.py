"""normalize product specifications into groups and parameters

Revision ID: fd8ceb1282c6
Revises: 85e9ed1bab8e
Create Date: 2026-11-03 17:51:45.640780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fd8ceb1282c6'
down_revision: Union[str, None] = '85e9ed1bab8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "specification_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "specification_parameters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("specification_groups.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(100), nullable=True, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("group_id", "name"),
    )
    op.create_index("ix_specification_parameters_group_id", "specification_parameters", ["group_id"])

    op.add_column("product_specifications", sa.Column("parameter_id", sa.Integer(), nullable=True))
    op.add_column("product_specifications", sa.Column("value", sa.String(500), nullable=True))

    op.execute("""
        INSERT INTO specification_groups (name, sort_order)
        SELECT btrim(group_name), MIN(sort_order)
        FROM product_specifications GROUP BY btrim(group_name)
    """)
    op.execute("""
        INSERT INTO specification_parameters (group_id, name, sort_order)
        SELECT g.id, btrim(ps.parameter_name), MIN(ps.sort_order)
        FROM product_specifications ps
        JOIN specification_groups g ON g.name = btrim(ps.group_name)
        GROUP BY g.id, btrim(ps.parameter_name)
    """)
    op.execute("""
        UPDATE product_specifications ps
        SET parameter_id = p.id, value = ps.parameter_value
        FROM specification_parameters p
        JOIN specification_groups g ON g.id = p.group_id
        WHERE g.name = btrim(ps.group_name) AND p.name = btrim(ps.parameter_name)
    """)

    op.alter_column("product_specifications", "parameter_id", nullable=False)
    op.create_foreign_key(
        "fk_product_specifications_parameter_id", "product_specifications",
        "specification_parameters", ["parameter_id"], ["id"], ondelete="RESTRICT",
    )
    op.create_index("ix_product_specifications_parameter_id", "product_specifications", ["parameter_id"])
    op.create_unique_constraint(
        "uq_product_specifications_product_parameter",
        "product_specifications", ["product_id", "parameter_id"],
    )
    for col in ("group_name", "parameter_name", "parameter_value", "sort_order"):
        op.drop_column("product_specifications", col)


def downgrade() -> None:
    op.add_column("product_specifications", sa.Column("group_name", sa.String(255), nullable=True))
    op.add_column("product_specifications", sa.Column("parameter_name", sa.String(500), nullable=True))
    op.add_column("product_specifications", sa.Column("parameter_value", sa.String(500), nullable=True))
    op.add_column("product_specifications", sa.Column("sort_order", sa.Integer(), nullable=True))

    op.execute("""
        UPDATE product_specifications ps
        SET group_name = g.name,
            parameter_name = p.name,
            parameter_value = ps.value
        FROM specification_parameters p
        JOIN specification_groups g ON g.id = p.group_id
        WHERE p.id = ps.parameter_id
    """)
    op.execute("""
        UPDATE product_specifications ps
        SET sort_order = r.rn
        FROM (
            SELECT s.id,
                   row_number() OVER (
                       PARTITION BY s.product_id
                       ORDER BY g.sort_order, p.sort_order, s.id
                   ) AS rn
            FROM product_specifications s
            JOIN specification_parameters p ON p.id = s.parameter_id
            JOIN specification_groups g ON g.id = p.group_id
        ) r
        WHERE r.id = ps.id
    """)

    op.alter_column("product_specifications", "group_name", nullable=False)
    op.alter_column("product_specifications", "parameter_name", nullable=False)
    op.alter_column("product_specifications", "sort_order", nullable=False)

    op.drop_constraint(
        "uq_product_specifications_product_parameter",
        "product_specifications",
        type_="unique",
    )
    op.drop_constraint(
        "fk_product_specifications_parameter_id",
        "product_specifications",
        type_="foreignkey",
    )
    op.drop_index("ix_product_specifications_parameter_id", table_name="product_specifications")
    op.drop_column("product_specifications", "parameter_id")
    op.drop_column("product_specifications", "value")

    op.drop_index("ix_specification_parameters_group_id", table_name="specification_parameters")
    op.drop_table("specification_parameters")
    op.drop_table("specification_groups")