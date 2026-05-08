"""Conversation CRUD and message handling with real LLM calls."""
import uuid
from typing import AsyncGenerator

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.engine.registry import get_provider
from app.models.api_key import ApiKey
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
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
            provider=data.provider,
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
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
        return conv

    async def update_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, data
    ) -> Conversation:
        conv = await self.get_conversation(user_id, conversation_id)
        if data.title is not None:
            conv.title = data.title
        if data.model_name is not None:
            conv.model_name = data.model_name
        if data.provider is not None:
            conv.provider = data.provider
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    async def delete_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> None:
        conv = await self.get_conversation(user_id, conversation_id)
        await self.db.delete(conv)
        await self.db.flush()

    async def _get_api_key(self, user_id: uuid.UUID, provider: str) -> tuple[str, str]:
        """Return (api_key, base_url) for the user + provider."""
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="对话未指定模型提供商",
            )
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.user_id == user_id,
                ApiKey.provider == provider,
                ApiKey.is_active == True,
            )
        )
        key = result.scalar_one_or_none()
        if not key or not key.api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"请先在模型配置中设置 {provider} 的 API Key",
            )
        return key.api_key, key.base_url or ""

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
        await self.db.flush()

        # Build message history
        messages = await self._build_messages(conv, data.content)

        # Get API key and call LLM
        api_key, base_url = await self._get_api_key(user_id, conv.provider)
        provider = get_provider(conv.provider, api_key, base_url)

        full_response = ""
        async for chunk in provider.generate_stream(messages, conv.model_name):
            full_response += chunk["token"]

        if not full_response:
            full_response = "(模型返回了空回复)"

        # Save assistant reply
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_response,
            token_count=len(full_response) // 2,
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
        return SendMessageResponse(role="assistant", content=full_response)

    async def send_message_stream(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, data: SendMessageRequest
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response via SSE. Yields SSE-formatted strings."""
        conv = await self.get_conversation(user_id, conversation_id)

        # Save user message
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=data.content,
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Build message history
        messages = await self._build_messages(conv, data.content)

        # Get API key and call LLM
        api_key, base_url = await self._get_api_key(user_id, conv.provider)
        provider = get_provider(conv.provider, api_key, base_url)

        full_response = ""
        try:
            async for chunk in provider.generate_stream(messages, conv.model_name):
                token = chunk["token"]
                full_response += token
                yield f"data: {token}\n\n"
        except Exception as e:
            error_msg = f"LLM 调用失败: {str(e)}"
            yield f"data: {error_msg}\n\n"

        if not full_response:
            full_response = "(模型返回了空回复)"

        # Save assistant reply
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_response,
            token_count=len(full_response) // 2,
        )
        self.db.add(assistant_msg)

        # Update counters
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

        yield "data: [DONE]\n\n"

    async def _build_messages(self, conv: Conversation, current_content: str) -> list[dict]:
        """Build LLM message list: system prompt + history + current user message."""
        messages: list[dict] = []
        if conv.system_prompt:
            messages.append({"role": "system", "content": conv.system_prompt})

        # Load previous messages (already saved, excluding the one we just added)
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
        )
        for msg in result.scalars().all():
            messages.append({"role": msg.role, "content": msg.content})

        return messages
