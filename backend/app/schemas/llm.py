"""Schemas for LLM factories and user-added models."""
from uuid import UUID

from pydantic import BaseModel, Field


# ── Factory JSON ──

class FactoryModelInfo(BaseModel):
    llm_name: str
    tags: str | None = None
    max_tokens: int | None = None
    model_type: str
    is_tools: bool = False


class FactoryInfo(BaseModel):
    name: str
    logo: str | None = None
    tags: str
    status: str = "1"
    rank: str = "0"
    url: str | None = None
    llm: list[FactoryModelInfo] = Field(default_factory=list)


# ── User-added Model ──

class LLMModelCreate(BaseModel):
    factory: str
    model_name: str
    model_type: str  # chat / embedding / rerank / image2text / speech2text / tts
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int | None = None
    is_tools: bool = False
    tags: str | None = None
    extra: str | None = None


class LLMModelUpdate(BaseModel):
    model_name: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    max_tokens: int | None = None
    is_tools: bool | None = None
    is_active: bool | None = None
    extra: str | None = None


class LLMModelOut(BaseModel):
    id: UUID
    factory: str
    model_type: str
    model_name: str
    api_key_masked: str | None = None
    base_url: str | None = None
    max_tokens: int | None = None
    is_tools: bool
    tags: str | None = None
    is_active: bool
    is_default: bool = False

    model_config = {"from_attributes": True}


# ── Default Models ──

class DefaultModelSet(BaseModel):
    model_type: str
    llm_model_id: UUID


class DefaultModelOut(BaseModel):
    model_type: str
    llm_model_id: UUID
    factory: str
    model_name: str
