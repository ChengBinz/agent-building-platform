"""add agent_id to conversations

Revision ID: a01b2c3d4e5f
Revises: dafedf348edb
Create Date: 2026-05-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a01b2c3d4e5f'
down_revision: Union[str, None] = 'dafedf348edb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('agent_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_conversations_agent_id'), 'conversations', ['agent_id'], unique=False)
    op.create_foreign_key(
        'fk_conversations_agent_id', 'conversations', 'agents',
        ['agent_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_conversations_agent_id', 'conversations', type_='foreignkey')
    op.drop_index(op.f('ix_conversations_agent_id'), table_name='conversations')
    op.drop_column('conversations', 'agent_id')
