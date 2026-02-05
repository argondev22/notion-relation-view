"""create initial schema for users, notion_tokens, and views

Revision ID: 4d05ea336494
Revises:
Create Date: 2026-02-05 11:10:26.023209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4d05ea336494'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  # Users table
  op.create_table(
    'users',
    sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
    sa.Column('email', sa.String(255), unique=True, nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('picture', sa.String(), nullable=True),
    sa.Column('plan', sa.String(10), nullable=False, server_default='free'),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
  )

  # Create index on email for faster lookups
  op.create_index('idx_users_email', 'users', ['email'])

  # Enforce plan values: only 'free' or 'pro' allowed
  op.create_check_constraint(
    'users_plan_check',
    'users',
    "plan IN ('free', 'pro')",
  )

  # Notion tokens table
  op.create_table(
    'notion_tokens',
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('encrypted_token', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

    # Foreign key constraint
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
  )

  # Views table
  op.create_table(
      'views',
      sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
      sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
      sa.Column('name', sa.String(255), nullable=False),
      sa.Column('database_ids', postgresql.ARRAY(sa.String()), nullable=False),
      sa.Column('zoom_level', sa.Float(), nullable=False, server_default='1.0'),
      sa.Column('pan_x', sa.Float(), nullable=False, server_default='0.0'),
      sa.Column('pan_y', sa.Float(), nullable=False, server_default='0.0'),
      sa.Column('extraction_mode', sa.String(20), nullable=False, server_default='property'),
      sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
      sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
      sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
  )

  # Create index on user_id for faster lookups
  op.create_index('idx_views_user_id', 'views', ['user_id'])

  # Enforce extraction_mode values
  op.create_check_constraint(
      'views_extraction_mode_check',
      'views',
      "extraction_mode IN ('property', 'mention', 'both')",
  )

def downgrade() -> None:
  # Drop tables in reverse order (child tables first)
  op.drop_table('views')
  op.drop_table('notion_tokens')
  op.drop_table('users')
