from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str = "新的智能体"
    description: str | None = None
    avatar: str | None = None
    system_prompt: str | None = None
    model_name: str = "gpt-4o-mini"
    provider: str = ""
    tools: list[str] | None = None
    kb_ids: list[UUID] | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    avatar: str | None = None
    system_prompt: str | None = None
    model_name: str | None = None
    provider: str | None = None
    tools: list[str] | None = None
    kb_ids: list[UUID] | None = None


class AgentOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    avatar: str | None = None
    system_prompt: str | None = None
    model_name: str
    provider: str
    tools: list[str] | None = None
    kb_ids: list[UUID] | None = None
    conversation_count: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentListItem(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    avatar: str | None = None
    model_name: str
    provider: str
    conversation_count: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
