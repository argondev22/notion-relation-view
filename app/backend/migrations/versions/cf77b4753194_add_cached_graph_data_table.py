"""add_cached_graph_data_table

Revision ID: cf77b4753194
Revises: 001
Create Date: 2026-01-25 08:01:53.293789

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf77b4753194'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cached_graph_data',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('cached_graph_data')
