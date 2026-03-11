"""Add latitude and longitude columns to property_listings

Revision ID: 002_add_geospatial
Revises: 001_initial
Create Date: 2026-03-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '002_add_geospatial'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if columns already exist before adding them
    bind = op.get_bind()
    inspector = inspect(bind)
    
    existing_columns = [col['name'] for col in inspector.get_columns('property_listings')]
    
    if 'latitude' not in existing_columns:
        op.add_column('property_listings', sa.Column('latitude', sa.Float(), nullable=True))
        op.create_index('ix_property_listings_latitude', 'property_listings', ['latitude'], unique=False)
    
    if 'longitude' not in existing_columns:
        op.add_column('property_listings', sa.Column('longitude', sa.Float(), nullable=True))
        op.create_index('ix_property_listings_longitude', 'property_listings', ['longitude'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_property_listings_longitude', table_name='property_listings')
    op.drop_column('property_listings', 'longitude')
    op.drop_index('ix_property_listings_latitude', table_name='property_listings')
    op.drop_column('property_listings', 'latitude')
