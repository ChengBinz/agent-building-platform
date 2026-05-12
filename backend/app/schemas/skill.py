from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    description: str | None = None
    skill_type: str = "prompt"
    content: str | None = None
    version: str = "1.0.0"


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    skill_type: str | None = None
    content: str | None = None
    version: str | None = None
    is_active: bool | None = None


class SkillOut(BaseModel):
    id: UUID
    user_id: UUID | None = None
    name: str
    description: str | None = None
    skill_type: str
    content: str | None = None
    is_system: bool
    is_active: bool
    version: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillToggle(BaseModel):
    is_active: bool
