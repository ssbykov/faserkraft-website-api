"""products is_published instead of status

Revision ID: 85e9ed1bab8e
Revises: 0cbbf87734f2
Create Date: 2026-11-03 15:00:56.799422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '85e9ed1bab8e'
down_revision: Union[str, None] = '0cbbf87734f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column('is_published', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )
    op.execute("UPDATE products SET is_published = (status = 'published')")
    op.create_index(op.f('ix_products_is_published'), 'products', ['is_published'], unique=False)
    op.drop_column('products', 'status')


def downgrade() -> None:
    op.add_column(
        'products',
        sa.Column(
            'status',
            sa.VARCHAR(length=50),
            server_default='published',
            autoincrement=False,
            nullable=False,
        ),
    )
    op.execute(
        "UPDATE products SET status = CASE WHEN is_published THEN 'published' ELSE 'draft' END"
    )
    op.drop_index(op.f('ix_products_is_published'), table_name='products')
    op.drop_column('products', 'is_published')
