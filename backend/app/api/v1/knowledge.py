"""Knowledge base CRUD and document management API."""
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.knowledge import (
    DocumentOut,
    DocumentUpload,
    KnowledgeBaseCreate,
    KnowledgeBaseListItem,
    KnowledgeBaseOut,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


# ── Knowledge Base CRUD ────────────────────────────────────────────


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


# ── Document Management ────────────────────────────────────────────


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=DocumentUpload,
    status_code=201,
)
async def upload_document(
    kb_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.upload_document(current_user.id, kb_id, file)


@router.get(
    "/knowledge-bases/{kb_id}/documents",
    response_model=list[DocumentOut],
)
async def list_documents(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.list_documents(current_user.id, kb_id)


@router.delete(
    "/knowledge-bases/{kb_id}/documents/{document_id}",
    status_code=204,
)
async def delete_document(
    kb_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    await service.delete_document(current_user.id, kb_id, document_id)
