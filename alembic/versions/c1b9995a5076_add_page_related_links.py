"""add page related links

Revision ID: c1b9995a5076
Revises: a9c375d834c5
Create Date: 2026-11-26 10:26:09.942096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1b9995a5076'
down_revision: Union[str, None] = 'a9c375d834c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('page_related_links',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('page_id', sa.Integer(), nullable=False),
    sa.Column('related_page_id', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(length=255), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.CheckConstraint('page_id <> related_page_id', name='ck_page_related_links_not_self'),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['related_page_id'], ['pages.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('page_id', 'related_page_id', name='uq_page_related_links_pair')
    )
    op.create_index(op.f('ix_page_related_links_page_id'), 'page_related_links', ['page_id'], unique=False)
    op.create_index(op.f('ix_page_related_links_related_page_id'), 'page_related_links', ['related_page_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_page_related_links_related_page_id'), table_name='page_related_links')
    op.drop_index(op.f('ix_page_related_links_page_id'), table_name='page_related_links')
    op.drop_table('page_related_links')
