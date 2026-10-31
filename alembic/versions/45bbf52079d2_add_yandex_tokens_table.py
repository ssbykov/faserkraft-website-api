"""add yandex tokens table

Revision ID: 45bbf52079d2
Revises: dc4bc921eeab
Create Date: 2026-10-31 19:16:02.073203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '45bbf52079d2'
down_revision: Union[str, None] = 'dc4bc921eeab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('yandex_tokens',
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('access_token', sa.String(), nullable=False),
    sa.Column('refresh_token', sa.String(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('yandex_tokens')
