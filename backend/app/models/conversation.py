import uuid

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.models.base import Base, UUIDMixin, TimestampMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="新的对话", nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), default="gpt-4o-mini", nullable=False)
    provider: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    kb_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), default=[])
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", lazy="selectin", order_by="Message.created_at",
        cascade="all, delete-orphan"
    )
