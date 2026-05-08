"""Monitoring request/response schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UsageSummary(BaseModel):
    total_conversations: int
    total_messages: int
    total_tokens: int
    total_documents: int
    active_users: int


class UsageTrendItem(BaseModel):
    date: str
    tokens: int
    requests: int


class TokenUsageByModel(BaseModel):
    model_name: str
    total_tokens: int
    request_count: int


class ModelConfig(BaseModel):
    name: str
    provider: str
    available: bool


class ProviderInfo(BaseModel):
    name: str
    configured: bool
    models: list[ModelConfig]
