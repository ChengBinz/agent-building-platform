import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import Agent
from app.models.conversation import Conversation
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_agents(self, user_id: uuid.UUID) -> list[Agent]:
        result = await self.db.execute(
            select(Agent)
            .options(selectinload(Agent.conversations))
            .where(Agent.user_id == user_id)
            .order_by(Agent.updated_at.desc())
        )
        return list(result.scalars().all())

    async def create_agent(self, user_id: uuid.UUID, data: AgentCreate) -> Agent:
        agent = Agent(
            user_id=user_id,
            name=data.name,
            description=data.description,
            avatar=data.avatar,
            system_prompt=data.system_prompt,
            model_name=data.model_name,
            provider=data.provider,
            tools=data.tools or [],
            kb_ids=data.kb_ids or [],
        )
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def get_agent(self, user_id: uuid.UUID, agent_id: uuid.UUID) -> Agent:
        result = await self.db.execute(
            select(Agent)
            .options(selectinload(Agent.conversations))
            .where(
                Agent.id == agent_id,
                Agent.user_id == user_id,
            )
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="智能体不存在")
        return agent

    async def update_agent(self, user_id: uuid.UUID, agent_id: uuid.UUID, data: AgentUpdate) -> Agent:
        agent = await self.get_agent(user_id, agent_id)
        if data.name is not None:
            agent.name = data.name
        if data.description is not None:
            agent.description = data.description
        if data.avatar is not None:
            agent.avatar = data.avatar
        if data.system_prompt is not None:
            agent.system_prompt = data.system_prompt
        if data.model_name is not None:
            agent.model_name = data.model_name
        if data.provider is not None:
            agent.provider = data.provider
        if data.tools is not None:
            agent.tools = data.tools
        if data.kb_ids is not None:
            agent.kb_ids = data.kb_ids
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def delete_agent(self, user_id: uuid.UUID, agent_id: uuid.UUID) -> None:
        agent = await self.get_agent(user_id, agent_id)
        await self.db.delete(agent)
        await self.db.flush()
