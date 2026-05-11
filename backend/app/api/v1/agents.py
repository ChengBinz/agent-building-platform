"""Agent CRUD API."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentUpdate, AgentOut, AgentListItem
from app.services.agent_service import AgentService

router = APIRouter()


def _conversation_count(agent) -> int:
    conversations = getattr(agent, "conversations", None)
    return len(conversations) if conversations is not None else 0


@router.get("/agents", response_model=list[AgentListItem])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    agents = await service.list_agents(current_user.id)
    return [
        AgentListItem(
            id=a.id,
            name=a.name,
            description=a.description,
            avatar=a.avatar,
            model_name=a.model_name,
            provider=a.provider,
            conversation_count=_conversation_count(a),
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in agents
    ]


@router.post("/agents", response_model=AgentOut, status_code=201)
async def create_agent(
    data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    agent = await service.create_agent(current_user.id, data)
    return AgentOut(
        id=agent.id,
        user_id=agent.user_id,
        name=agent.name,
        description=agent.description,
        avatar=agent.avatar,
        system_prompt=agent.system_prompt,
        model_name=agent.model_name,
        provider=agent.provider,
        tools=agent.tools,
        kb_ids=agent.kb_ids,
        conversation_count=0,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.get("/agents/{agent_id}", response_model=AgentOut)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    agent = await service.get_agent(current_user.id, agent_id)
    return AgentOut(
        id=agent.id,
        user_id=agent.user_id,
        name=agent.name,
        description=agent.description,
        avatar=agent.avatar,
        system_prompt=agent.system_prompt,
        model_name=agent.model_name,
        provider=agent.provider,
        tools=agent.tools,
        kb_ids=agent.kb_ids,
        conversation_count=_conversation_count(agent),
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.patch("/agents/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    agent = await service.update_agent(current_user.id, agent_id, data)
    return AgentOut(
        id=agent.id,
        user_id=agent.user_id,
        name=agent.name,
        description=agent.description,
        avatar=agent.avatar,
        system_prompt=agent.system_prompt,
        model_name=agent.model_name,
        provider=agent.provider,
        tools=agent.tools,
        kb_ids=agent.kb_ids,
        conversation_count=_conversation_count(agent),
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AgentService(db)
    await service.delete_agent(current_user.id, agent_id)
