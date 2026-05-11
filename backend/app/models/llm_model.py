"""User-configured LLM model entries (RAGFlow-style)."""
import uuid

from sqlalchemy import Boolean, Integer, String, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, UUIDMixin, TimestampMixin


class LLMModel(Base, UUIDMixin, TimestampMixin):
    """A concrete model configuration added by a user.

    One user can have multiple rows for the same factory — e.g. two different
    OpenAI-compatible endpoints, or the same provider but different model names.
    """

    __tablename__ = "llm_models"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "factory", "model_name", "model_type",
            name="uq_llm_models_user_factory_model",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # factory identifier from llm_factories.json (e.g. "OpenAI", "DeepSeek")
    factory: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # chat / embedding / rerank / image2text / speech2text / tts
    model_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    api_key: Mapped[str | None] = mapped_column(Text)
    base_url: Mapped[str | None] = mapped_column(String(512))
    max_tokens: Mapped[int | None] = mapped_column(Integer)
    is_tools: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[str | None] = mapped_column(String(255))
    # extra JSON-like fields (deployment name for Azure, region for Bedrock, …)
    # kept as simple text for now, can be promoted to JSONB later
    extra: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship()


class DefaultModel(Base, UUIDMixin, TimestampMixin):
    """Per-user default model for each model_type (chat/embedding/rerank/…)."""

    __tablename__ = "default_models"
    __table_args__ = (
        UniqueConstraint("user_id", "model_type", name="uq_default_models_user_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_type: Mapped[str] = mapped_column(String(32), nullable=False)
    llm_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("llm_models.id", ondelete="CASCADE"), nullable=False
    )
