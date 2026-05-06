"""Usage stats aggregation."""
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.models.usage_log import UsageLog
from app.models.user import User
from app.schemas.monitoring import UsageSummary, TokenUsageByModel


class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usage_summary(self) -> UsageSummary:
        total_conversations = (
            await self.db.scalar(select(func.count(Conversation.id)))
        ) or 0
        total_messages = (
            await self.db.scalar(select(func.count(Message.id)))
        ) or 0
        total_tokens = (
            await self.db.scalar(
                select(func.coalesce(func.sum(Conversation.total_tokens), 0))
            )
        ) or 0
        total_documents = (
            await self.db.scalar(select(func.count(Document.id)))
        ) or 0
        active_users = (
            await self.db.scalar(
                select(func.count(User.id)).where(User.is_active == True)
            )
        ) or 0

        return UsageSummary(
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_tokens=total_tokens,
            total_documents=total_documents,
            active_users=active_users,
        )

    async def get_usage_by_model(self) -> list[TokenUsageByModel]:
        result = await self.db.execute(
            select(
                UsageLog.model_name,
                func.sum(UsageLog.total_tokens).label("total_tokens"),
                func.count(UsageLog.id).label("request_count"),
            )
            .group_by(UsageLog.model_name)
            .order_by(func.sum(UsageLog.total_tokens).desc())
            .limit(10)
        )
        return [
            TokenUsageByModel(
                model_name=row.model_name,
                total_tokens=row.total_tokens or 0,
                request_count=row.request_count,
            )
            for row in result.all()
        ]
