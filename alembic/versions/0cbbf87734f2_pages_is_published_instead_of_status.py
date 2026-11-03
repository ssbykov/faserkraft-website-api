"""pages is_published instead of status

Revision ID: 0cbbf87734f2
Revises: 4ab07b55cc93
Create Date: 2026-11-03 14:30:39.038574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0cbbf87734f2'
down_revision: Union[str, None] = '4ab07b55cc93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'pages',
        sa.Column('is_published', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )
    op.execute("UPDATE pages SET is_published = (status = 'published')")
    op.create_index(op.f('ix_pages_is_published'), 'pages', ['is_published'], unique=False)
    op.drop_column('pages', 'status')


def downgrade() -> None:
    op.add_column(
        'pages',
        sa.Column(
            'status',
            sa.VARCHAR(length=50),
            server_default='published',
            autoincrement=False,
            nullable=False,
        ),
    )
    op.execute(
        "UPDATE pages SET status = CASE WHEN is_published THEN 'published' ELSE 'draft' END"
    )
    op.drop_index(op.f('ix_pages_is_published'), table_name='pages')
    op.drop_column('pages', 'is_published')
