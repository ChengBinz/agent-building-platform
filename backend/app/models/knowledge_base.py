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
    embedding_model: Mapped[str] = mapped_column(String(128), default="text-embedding-v4", nullable=False)
    embedding_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base", lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def embedding_api_key_masked(self) -> str | None:
        if not self.embedding_api_key:
            return None
        return "****" + self.embedding_api_key[-4:]
