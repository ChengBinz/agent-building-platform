"""Knowledge base CRUD and document management."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_knowledge_bases(self, user_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.user_id == user_id)
            .order_by(KnowledgeBase.updated_at.desc())
        )
        kbs = result.scalars().all()
        # Attach document_count to each item
        out = []
        for kb in kbs:
            doc_count = await self.db.scalar(
                select(func.count(Document.id)).where(Document.kb_id == kb.id)
            )
            kb_dict = {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "embedding_model": kb.embedding_model,
                "chunk_count": kb.chunk_count,
                "document_count": doc_count or 0,
                "created_at": kb.created_at,
                "updated_at": kb.updated_at,
            }
            out.append(kb_dict)
        return out

    async def create_knowledge_base(
        self, user_id: uuid.UUID, data: KnowledgeBaseCreate
    ) -> KnowledgeBase:
        kb = KnowledgeBase(
            user_id=user_id,
            name=data.name,
            description=data.description,
            embedding_model=data.embedding_model,
        )
        self.db.add(kb)
        await self.db.flush()
        await self.db.refresh(kb)
        return kb

    async def get_knowledge_base(
        self, user_id: uuid.UUID, kb_id: uuid.UUID
    ) -> KnowledgeBase:
        result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        kb = result.scalar_one_or_none()
        if kb is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在"
            )
        return kb

    async def update_knowledge_base(
        self, user_id: uuid.UUID, kb_id: uuid.UUID, data: KnowledgeBaseUpdate
    ) -> KnowledgeBase:
        kb = await self.get_knowledge_base(user_id, kb_id)
        if data.name is not None:
            kb.name = data.name
        if data.description is not None:
            kb.description = data.description
        await self.db.flush()
        await self.db.refresh(kb)
        return kb

    async def delete_knowledge_base(
        self, user_id: uuid.UUID, kb_id: uuid.UUID
    ) -> None:
        kb = await self.get_knowledge_base(user_id, kb_id)
        await self.db.delete(kb)
        await self.db.flush()
