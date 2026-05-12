import uuid

from sqlalchemy import Boolean, String, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roles: Mapped[list["Role"]] = relationship(secondary=user_roles, lazy="selectin")
    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="user", lazy="selectin", passive_deletes=True)
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user", lazy="selectin", passive_deletes=True)
    agents: Mapped[list["Agent"]] = relationship(back_populates="user", lazy="selectin", passive_deletes=True)
    mcp_servers: Mapped[list["MCPServer"]] = relationship(back_populates="user", lazy="selectin", passive_deletes=True)


class Role(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))


class UserRole(Base):
    """Explicit ORM mapping for user_roles association table (for queries)."""
    __table__ = user_roles
