"""Knowledge base CRUD and document management."""
import asyncio
import logging
import os
import shutil
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/data/uploads"

# Keep strong references to background tasks to prevent garbage collection
_background_tasks: set[asyncio.Task] = set()


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Knowledge Base CRUD ────────────────────────────────────────

    async def list_knowledge_bases(self, user_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.user_id == user_id)
            .order_by(KnowledgeBase.updated_at.desc())
        )
        kbs = result.scalars().all()
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
            embedding_api_key=data.embedding_api_key,
            embedding_base_url=data.embedding_base_url,
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
        if data.embedding_model is not None:
            kb.embedding_model = data.embedding_model
        if data.embedding_api_key is not None:
            kb.embedding_api_key = data.embedding_api_key
        if data.embedding_base_url is not None:
            kb.embedding_base_url = data.embedding_base_url
        await self.db.flush()
        await self.db.refresh(kb)
        return kb

    async def delete_knowledge_base(
        self, user_id: uuid.UUID, kb_id: uuid.UUID
    ) -> None:
        kb = await self.get_knowledge_base(user_id, kb_id)

        # Delete Qdrant collection
        try:
            from app.rag.pipeline import delete_kb_collection
            await delete_kb_collection(kb_id)
        except Exception as e:
            logger.warning(f"Failed to delete Qdrant collection for KB {kb_id}: {e}")

        # Delete upload directory
        kb_dir = os.path.join(UPLOAD_DIR, str(kb_id))
        try:
            if os.path.exists(kb_dir):
                shutil.rmtree(kb_dir)
        except Exception as e:
            logger.warning(f"Failed to delete upload dir {kb_dir}: {e}")

        await self.db.delete(kb)
        await self.db.flush()

    # ── Document Management ────────────────────────────────────────

    async def upload_document(
        self, user_id: uuid.UUID, kb_id: uuid.UUID, file: UploadFile
    ) -> Document:
        kb = await self.get_knowledge_base(user_id, kb_id)

        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in {".txt", ".md", ".pdf", ".docx", ".csv"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仅支持 .txt、.md、.pdf、.docx 和 .csv 文件",
            )

        content = await file.read()

        # Save to disk
        kb_dir = os.path.join(UPLOAD_DIR, str(kb_id))
        os.makedirs(kb_dir, exist_ok=True)

        safe_name = file.filename or "unnamed.txt"
        file_path = os.path.join(kb_dir, safe_name)
        if os.path.exists(file_path):
            base, ext_part = os.path.splitext(safe_name)
            counter = 1
            while os.path.exists(file_path):
                safe_name = f"{base}_{counter}{ext_part}"
                file_path = os.path.join(kb_dir, safe_name)
                counter += 1

        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            kb_id=kb_id,
            filename=safe_name,
            file_type=ext.lstrip("."),
            file_size=len(content),
            status="pending",
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        await self.db.commit()

        from app.rag.pipeline import ingest_document

        task = asyncio.create_task(ingest_document(file_path, doc.id, kb_id, safe_name))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)
        task.add_done_callback(self._handle_task_exception)

        return doc

    async def list_documents(
        self, user_id: uuid.UUID, kb_id: uuid.UUID
    ) -> list[Document]:
        await self.get_knowledge_base(user_id, kb_id)
        result = await self.db.execute(
            select(Document)
            .where(Document.kb_id == kb_id)
            .order_by(Document.id.desc())
        )
        return list(result.scalars().all())

    async def delete_document(
        self, user_id: uuid.UUID, kb_id: uuid.UUID, document_id: uuid.UUID
    ) -> None:
        await self.get_knowledge_base(user_id, kb_id)

        result = await self.db.execute(
            select(Document).where(Document.id == document_id, Document.kb_id == kb_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在"
            )

        # Remove vectors from Qdrant
        if doc.qdrant_point_ids:
            try:
                from app.rag.pipeline import delete_document_vectors
                await delete_document_vectors(kb_id, doc.qdrant_point_ids)
            except Exception as e:
                logger.warning(f"Failed to delete Qdrant points for doc {doc.id}: {e}")

        # Remove file from disk
        file_path = os.path.join(UPLOAD_DIR, str(kb_id), doc.filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")

        # Update KB chunk_count
        kb_result = await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = kb_result.scalar_one_or_none()
        if kb:
            remaining = await self.db.scalar(
                select(func.coalesce(func.sum(Document.chunk_count), 0)).where(
                    Document.kb_id == kb_id,
                    Document.status == "completed",
                    Document.id != document_id,
                )
            )
            kb.chunk_count = remaining or 0

        await self.db.delete(doc)
        await self.db.flush()

    @staticmethod
    def _handle_task_exception(task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.exception(f"Background ingestion task failed: {exc}", exc_info=exc)
