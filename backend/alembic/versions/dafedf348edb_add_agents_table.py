"""add agents table and provider column

Revision ID: dafedf348edb
Revises: c08034b509c1
Create Date: 2026-05-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'dafedf348edb'
down_revision: Union[str, None] = 'c08034b509c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('agents',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('avatar', sa.String(length=512), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=128), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('tools', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('kb_ids', postgresql.ARRAY(sa.UUID()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_user_id'), 'agents', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agents_user_id'), table_name='agents')
    op.drop_table('agents')
