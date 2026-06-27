"""Per-conversation memory summary (LLM-generated rolling summary)."""
import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, UUIDMixin, TimestampMixin


class ConversationMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversation_memories"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 记录这次摘要覆盖到第几条消息（用于增量摘要时的进度跟踪）
    summarized_up_to: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
