"""add product.min_stock_level and sale.product_sku

Revision ID: 0001
Revises: 
Create Date: 2026-06-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add min_stock_level to product (default 5)
    op.add_column('product', sa.Column('min_stock_level', sa.Integer(), nullable=False, server_default=sa.text('5')))

    # Add product_sku to sale
    op.add_column('sale', sa.Column('product_sku', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('sale', 'product_sku')
    op.drop_column('product', 'min_stock_level')
