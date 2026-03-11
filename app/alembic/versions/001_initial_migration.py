"""Initial migration - create property_listings table

Revision ID: 001_initial
Revises: 
Create Date: 2026-03-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists (for existing deployments)
    bind = op.get_bind()
    inspector = inspect(bind)
    
    if 'property_listings' not in inspector.get_table_names():
        op.create_table(
            'property_listings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('address', sa.String(), nullable=False),
            sa.Column('postcode', sa.String(), nullable=False),
            sa.Column('price', sa.Integer(), nullable=False),
            sa.Column('property_type', sa.String(), nullable=False),
            sa.Column('bedrooms', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_property_listings_id', 'property_listings', ['id'], unique=False)
        op.create_index('ix_property_listings_postcode', 'property_listings', ['postcode'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_property_listings_postcode', table_name='property_listings')
    op.drop_index('ix_property_listings_id', table_name='property_listings')
    op.drop_table('property_listings')
