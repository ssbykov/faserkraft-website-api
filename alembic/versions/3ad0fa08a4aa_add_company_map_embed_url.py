"""add company map embed url

Revision ID: 3ad0fa08a4aa
Revises: 3fc63b2631da
Create Date: 2026-11-21 17:07:19.906603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3ad0fa08a4aa'
down_revision: Union[str, None] = '3fc63b2631da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('company_info', sa.Column('map_embed_url', sa.String(length=2000), nullable=True))


def downgrade() -> None:
    op.drop_column('company_info', 'map_embed_url')
