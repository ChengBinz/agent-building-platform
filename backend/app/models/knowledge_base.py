import uuid

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, UUIDMixin, TimestampMixin


class KnowledgeBase(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_bases"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    embedding_model: Mapped[str] = mapped_column(String(128), default="text-embedding-3-small", nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base", lazy="selectin"
    )
