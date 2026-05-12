from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


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

    @field_validator("auth_value", mode="before")
    @classmethod
    def mask_auth_value(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if len(v) <= 4:
            return "****"
        return "*" * (len(v) - 4) + v[-4:]


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
