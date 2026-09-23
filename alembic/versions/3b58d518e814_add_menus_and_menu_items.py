"""add menus and menu items

Revision ID: 3b58d518e814
Revises: 4d8491a69cd1
Create Date: 2026-09-23 12:56:14.855662

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3b58d518e814'
down_revision: Union[str, None] = '4d8491a69cd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('menus',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=100), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menus_code'), 'menus', ['code'], unique=True)
    op.create_table('menu_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('menu_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('page_id', sa.Integer(), nullable=True),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(length=1000), nullable=True),
    sa.Column('label', sa.String(length=255), nullable=False),
    sa.Column('target_blank', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    sa.Column('is_visible', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("\n            (\n                CASE WHEN page_id IS NOT NULL THEN 1 ELSE 0 END +\n                CASE WHEN product_id IS NOT NULL THEN 1 ELSE 0 END +\n                CASE WHEN url IS NOT NULL AND url <> '' THEN 1 ELSE 0 END\n            ) <= 1\n            ", name='ck_menu_items_one_link_source'),
    sa.ForeignKeyConstraint(['menu_id'], ['menus.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['page_id'], ['pages.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['parent_id'], ['menu_items.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_items_menu_id'), 'menu_items', ['menu_id'], unique=False)
    op.create_index(op.f('ix_menu_items_page_id'), 'menu_items', ['page_id'], unique=False)
    op.create_index(op.f('ix_menu_items_parent_id'), 'menu_items', ['parent_id'], unique=False)
    op.create_index(op.f('ix_menu_items_product_id'), 'menu_items', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_menu_items_product_id'), table_name='menu_items')
    op.drop_index(op.f('ix_menu_items_parent_id'), table_name='menu_items')
    op.drop_index(op.f('ix_menu_items_page_id'), table_name='menu_items')
    op.drop_index(op.f('ix_menu_items_menu_id'), table_name='menu_items')
    op.drop_table('menu_items')
    op.drop_index(op.f('ix_menus_code'), table_name='menus')
    op.drop_table('menus')
