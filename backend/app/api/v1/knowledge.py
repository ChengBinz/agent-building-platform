"""Knowledge base CRUD API."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseOut,
    KnowledgeBaseListItem,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseListItem])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.list_knowledge_bases(current_user.id)


@router.post("/knowledge-bases", response_model=KnowledgeBaseOut, status_code=201)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.create_knowledge_base(current_user.id, data)


@router.get("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.get_knowledge_base(current_user.id, kb_id)


@router.put("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseOut)
async def update_knowledge_base(
    kb_id: uuid.UUID,
    data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.update_knowledge_base(current_user.id, kb_id, data)


@router.delete("/knowledge-bases/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    await service.delete_knowledge_base(current_user.id, kb_id)
