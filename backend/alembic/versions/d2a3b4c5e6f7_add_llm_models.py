"""add llm_models and default_models tables

Revision ID: d2a3b4c5e6f7
Revises: b1c2d3e4f5a6
Create Date: 2025-05-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "d2a3b4c5e6f7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("factory", sa.String(64), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("api_key", sa.Text()),
        sa.Column("base_url", sa.String(512)),
        sa.Column("max_tokens", sa.Integer()),
        sa.Column("is_tools", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tags", sa.String(255)),
        sa.Column("extra", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "factory", "model_name", "model_type", name="uq_llm_models_user_factory_model"),
    )
    op.create_index("ix_llm_models_user_id", "llm_models", ["user_id"])
    op.create_index("ix_llm_models_factory", "llm_models", ["factory"])
    op.create_index("ix_llm_models_model_type", "llm_models", ["model_type"])

    op.create_table(
        "default_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("llm_model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("llm_models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "model_type", name="uq_default_models_user_type"),
    )
    op.create_index("ix_default_models_user_id", "default_models", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_default_models_user_id", table_name="default_models")
    op.drop_table("default_models")
    op.drop_index("ix_llm_models_model_type", table_name="llm_models")
    op.drop_index("ix_llm_models_factory", table_name="llm_models")
    op.drop_index("ix_llm_models_user_id", table_name="llm_models")
    op.drop_table("llm_models")
