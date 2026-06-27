"""add summarized_up_to to conversation_memories

Revision ID: 3b7f1e2c4d51
Revises: 251a05db90b7
Create Date: 2026-06-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3b7f1e2c4d51"
down_revision: Union[str, None] = "251a05db90b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_memories",
        sa.Column(
            "summarized_up_to",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("conversation_memories", "summarized_up_to")
