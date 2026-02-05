"""add_cached_database_data_table

Revision ID: a73610f840b2
Revises: cf77b4753194
Create Date: 2026-01-26 00:56:31.922582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a73610f840b2'
down_revision = 'cf77b4753194'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cached_database_data table with composite primary key
    op.create_table(
        'cached_database_data',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('database_id', sa.String(255), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'database_id')
    )

    # Create indexes for efficient lookups
    op.create_index(
        'ix_cached_db_user_db',
        'cached_database_data',
        ['user_id', 'database_id']
    )

    op.create_index(
        'ix_cached_db_expires',
        'cached_database_data',
        ['expires_at']
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_cached_db_expires', 'cached_database_data')
    op.drop_index('ix_cached_db_user_db', 'cached_database_data')

    # Drop table
    op.drop_table('cached_database_data')
