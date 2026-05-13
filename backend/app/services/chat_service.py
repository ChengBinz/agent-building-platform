"""Chat service facade — delegates to ConversationService and MessageService."""
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.schemas.chat import (
    ConversationCreate,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService


class ChatService:
    """Thin facade that preserves the existing API contract for chat.py."""

    def __init__(self, db: AsyncSession):
        self._conversation = ConversationService(db)
        self._message = MessageService(db)

    # ── Conversation CRUD (delegated to ConversationService) ──

    async def list_conversations(
        self, user_id: uuid.UUID, agent_id: uuid.UUID | None = None
    ) -> list[Conversation]:
        return await self._conversation.list_conversations(user_id, agent_id)

    async def create_conversation(
        self, user_id: uuid.UUID, data: ConversationCreate
    ) -> Conversation:
        return await self._conversation.create_conversation(user_id, data)

    async def get_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Conversation:
        return await self._conversation.get_conversation(user_id, conversation_id)

    async def update_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, data
    ) -> Conversation:
        return await self._conversation.update_conversation(
            user_id, conversation_id, data
        )

    async def delete_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> None:
        return await self._conversation.delete_conversation(
            user_id, conversation_id
        )

    # ── Message sending (delegated to MessageService) ──

    async def send_message(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        data: SendMessageRequest,
    ) -> SendMessageResponse:
        return await self._message.send_message(user_id, conversation_id, data)

    async def send_message_stream(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        data: SendMessageRequest,
    ) -> AsyncGenerator[str, None]:
        async for chunk in self._message.send_message_stream(
            user_id, conversation_id, data
        ):
            yield chunk
