"""Knowledge base request/response schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str | None = None
    embedding_model: str = "text-embedding-3-small"


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: str | None = None

    model_config = {"from_attributes": True}


class KnowledgeBaseOut(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    embedding_model: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    documents: list[DocumentOut] = []

    model_config = {"from_attributes": True}


class KnowledgeBaseListItem(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    embedding_model: str
    chunk_count: int
    document_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
