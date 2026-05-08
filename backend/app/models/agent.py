import uuid

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.models.base import Base, UUIDMixin, TimestampMixin


class Agent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    avatar: Mapped[str | None] = mapped_column(String(512))
    system_prompt: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(128), default="gpt-4o-mini", nullable=False)
    provider: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    tools: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=[])
    kb_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), default=[])

    user: Mapped["User"] = relationship(back_populates="agents")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="agent", lazy="selectin", order_by="Conversation.updated_at.desc()",
        passive_deletes=True
    )
