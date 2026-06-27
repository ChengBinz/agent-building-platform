"""make messages.content nullable for tool-call rows

Revision ID: 4c8a9d2e6f33
Revises: 3b7f1e2c4d51
Create Date: 2026-06-28 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c8a9d2e6f33"
down_revision: Union[str, None] = "3b7f1e2c4d51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 当 assistant 仅返回 tool_calls 而无文本时 content 会是 NULL
    op.alter_column(
        "messages",
        "content",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    # 回滚时先把 NULL 改成空字符串，避免回滚失败
    op.execute("UPDATE messages SET content = '' WHERE content IS NULL")
    op.alter_column(
        "messages",
        "content",
        existing_type=sa.Text(),
        nullable=False,
    )
