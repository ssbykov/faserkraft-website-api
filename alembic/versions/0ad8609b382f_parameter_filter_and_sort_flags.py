"""parameter filter and sort flags

Revision ID: 0ad8609b382f
Revises: fd8ceb1282c6
Create Date: 2026-11-05 11:09:28.034328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0ad8609b382f'
down_revision: Union[str, None] = 'fd8ceb1282c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('specification_parameters', sa.Column('is_filterable', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('specification_parameters', sa.Column('list_sort_order', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('specification_parameters', 'list_sort_order')
    op.drop_column('specification_parameters', 'is_filterable')
