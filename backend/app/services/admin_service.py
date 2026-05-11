"""User management, system settings."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.user import User
from app.models.conversation import Conversation
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.usage_log import UsageLog
from app.schemas.auth import UserResponse


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
        )
        users = [UserResponse.model_validate(u) for u in result.scalars().all()]
        total = await self.db.scalar(select(func.count(User.id))) or 0
        return {"items": users, "total": total, "page": page, "page_size": page_size}

    async def get_user(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(
            select(User)
            .options(noload(User.conversations), noload(User.agents), noload(User.api_keys))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        return user

    async def _count_active_superusers(self, exclude_id: uuid.UUID | None = None) -> int:
        query = select(func.count(User.id)).where(
            User.is_active == True, User.is_superuser == True
        )
        if exclude_id is not None:
            query = query.where(User.id != exclude_id)
        return await self.db.scalar(query) or 0

    async def _ensure_not_last_admin(self, user: User) -> None:
        """Raise if user is the last active superuser (prevents lockout)."""
        if user.is_active and user.is_superuser:
            remaining = await self._count_active_superusers(exclude_id=user.id)
            if remaining == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法操作：至少需要保留一个启用的管理员账号",
                )

    async def update_user_status(
        self, user_id: uuid.UUID, is_active: bool | None = None, is_superuser: bool | None = None
    ) -> User:
        user = await self.get_user(user_id)

        # If disabling or removing superuser, ensure it's not the last admin
        if is_active is False or is_superuser is False:
            await self._ensure_not_last_admin(user)

        if is_active is not None:
            user.is_active = is_active
        if is_superuser is not None:
            user.is_superuser = is_superuser
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self.get_user(user_id)
        await self._ensure_not_last_admin(user)
        await self.db.delete(user)
        await self.db.flush()

    async def get_system_stats(self) -> dict:
        user_count = await self.db.scalar(select(func.count(User.id))) or 0
        conv_count = await self.db.scalar(select(func.count(Conversation.id))) or 0
        kb_count = await self.db.scalar(select(func.count(KnowledgeBase.id))) or 0
        doc_count = await self.db.scalar(select(func.count(Document.id))) or 0
        total_tokens = (
            await self.db.scalar(
                select(func.coalesce(func.sum(UsageLog.total_tokens), 0))
            )
        ) or 0

        return {
            "user_count": user_count,
            "conversation_count": conv_count,
            "knowledge_base_count": kb_count,
            "document_count": doc_count,
            "total_tokens": total_tokens,
        }
