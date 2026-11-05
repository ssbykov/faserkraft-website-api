"""product card fields

Revision ID: 1321a5463f81
Revises: 0ad8609b382f
Create Date: 2026-11-05 14:17:08.578017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1321a5463f81'
down_revision: Union[str, None] = '0ad8609b382f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('product_card_fields',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=50), nullable=False),
    sa.Column('label', sa.String(length=100), nullable=True),
    sa.Column('parameter_id', sa.Integer(), nullable=False),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.ForeignKeyConstraint(['parameter_id'], ['specification_parameters.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('key')
    )
    op.create_index(op.f('ix_product_card_fields_parameter_id'), 'product_card_fields', ['parameter_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_card_fields_parameter_id'), table_name='product_card_fields')
    op.drop_table('product_card_fields')
