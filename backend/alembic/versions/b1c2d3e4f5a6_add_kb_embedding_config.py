"""add embedding_api_key and embedding_base_url to knowledge_bases

Revision ID: b1c2d3e4f5a6
Revises: a01b2c3d4e5f
Create Date: 2026-05-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a01b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('knowledge_bases', sa.Column('embedding_api_key', sa.Text(), nullable=True))
    op.add_column('knowledge_bases', sa.Column('embedding_base_url', sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column('knowledge_bases', 'embedding_base_url')
    op.drop_column('knowledge_bases', 'embedding_api_key')
