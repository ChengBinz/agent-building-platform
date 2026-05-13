"""Conversation CRUD operations."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import Agent
from app.models.conversation import Conversation
from app.schemas.chat import ConversationCreate


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_conversations(
        self, user_id: uuid.UUID, agent_id: uuid.UUID | None = None
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        if agent_id:
            stmt = stmt.where(Conversation.agent_id == agent_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_conversation(
        self, user_id: uuid.UUID, data: ConversationCreate
    ) -> Conversation:
        model_name = data.model_name
        provider = data.provider
        system_prompt = data.system_prompt
        kb_ids = None

        if data.agent_id:
            result = await self.db.execute(
                select(Agent).where(Agent.id == data.agent_id, Agent.user_id == user_id)
            )
            agent = result.scalar_one_or_none()
            if agent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="智能体不存在"
                )
            model_name = model_name or agent.model_name
            provider = provider or agent.provider
            system_prompt = system_prompt or agent.system_prompt
            kb_ids = agent.kb_ids

        conv = Conversation(
            user_id=user_id,
            agent_id=data.agent_id,
            title=data.title,
            model_name=model_name,
            provider=provider,
            system_prompt=system_prompt,
            kb_ids=kb_ids,
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
            .options(
                selectinload(Conversation.messages), selectinload(Conversation.agent)
            )
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在"
            )
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
