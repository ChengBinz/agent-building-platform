"""Chat request/response schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str = "新的对话"
    model_name: str = "deepseek-v4-flash"
    provider: str = "deepseek"
    system_prompt: str | None = None
    agent_id: UUID | None = None


class ConversationUpdate(BaseModel):
    title: str | None = None
    model_name: str | None = None
    provider: str | None = None
    agent_id: UUID | None = None


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    token_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: UUID
    agent_id: UUID | None = None
    title: str
    model_name: str
    provider: str = ""
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    id: UUID
    agent_id: UUID | None = None
    title: str
    model_name: str
    provider: str = ""
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str
    enable_web_search: bool = False


class SendMessageResponse(BaseModel):
    role: str
    content: str
