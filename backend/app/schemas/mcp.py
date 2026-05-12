from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MCPServerCreate(BaseModel):
    name: str
    url: str
    transport: str = "sse"
    auth_type: str = "none"
    auth_value: str | None = None
    is_active: bool = True


class MCPServerUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    transport: str | None = None
    auth_type: str | None = None
    auth_value: str | None = None
    is_active: bool | None = None


class MCPServerOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    url: str
    transport: str
    auth_type: str
    auth_value: str | None = None
    is_active: bool
    tool_count: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MCPToolOut(BaseModel):
    id: UUID
    server_id: UUID
    user_id: UUID
    name: str
    description: str | None = None
    input_schema: dict | None = None
    is_active: bool
    server_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MCPToolToggle(BaseModel):
    is_active: bool
