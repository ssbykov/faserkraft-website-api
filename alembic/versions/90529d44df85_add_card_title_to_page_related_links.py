"""add card title to page related links

Revision ID: 90529d44df85
Revises: c1b9995a5076
Create Date: 2026-11-26 13:12:31.368151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '90529d44df85'
down_revision: Union[str, None] = 'c1b9995a5076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('page_related_links', sa.Column('card_title', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('page_related_links', 'card_title')

