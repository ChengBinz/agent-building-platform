"""Conversation CRUD and message handling."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ConversationCreate,
    SendMessageRequest,
    SendMessageResponse,
)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_conversations(self, user_id: uuid.UUID) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def create_conversation(
        self, user_id: uuid.UUID, data: ConversationCreate
    ) -> Conversation:
        conv = Conversation(
            user_id=user_id,
            title=data.title,
            model_name=data.model_name,
            system_prompt=data.system_prompt,
        )
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    async def get_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Conversation:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
        return conv

    async def delete_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> None:
        conv = await self.get_conversation(user_id, conversation_id)
        await self.db.delete(conv)
        await self.db.flush()

    async def send_message(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, data: SendMessageRequest
    ) -> SendMessageResponse:
        conv = await self.get_conversation(user_id, conversation_id)

        # Save user message
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=data.content,
        )
        self.db.add(user_msg)

        # Generate a placeholder assistant reply (real implementation calls LLM)
        assistant_reply = (
            f"收到您的消息：「{data.content}」\n\n"
            f"当前模型：{conv.model_name}\n"
            f"这是一个占位回复。接入 LLM API 后可获得真实回复。"
        )
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=assistant_reply,
            token_count=len(assistant_reply) // 2,
        )
        self.db.add(assistant_msg)

        # Update conversation counters
        conv.message_count = (
            await self.db.scalar(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conv.id
                )
            )
            or 0
        )
        conv.total_tokens = (
            await self.db.scalar(
                select(func.coalesce(func.sum(Message.token_count), 0)).where(
                    Message.conversation_id == conv.id
                )
            )
            or 0
        )

        await self.db.flush()
        return SendMessageResponse(role="assistant", content=assistant_reply)
