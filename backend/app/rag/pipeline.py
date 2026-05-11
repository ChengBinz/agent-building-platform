"""End-to-end document ingestion and cleanup."""
import logging
import traceback
import uuid

from sqlalchemy import select, func

from app.config import settings
from app.db.session import async_session_factory
from app.models.api_key import ApiKey
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.rag.chunker import chunk_text
from app.rag.embedder import embed_texts, get_embedding_client
from app.rag.loader import load_text
from app.rag.vector_store import (
    delete_collection,
    delete_points_by_ids,
    ensure_collection,
    get_qdrant_client,
    upsert_points,
)
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)


async def ingest_document(
    file_path: str, document_id: uuid.UUID, kb_id: uuid.UUID, filename: str
) -> None:
    """Background task: load → chunk → embed → store in Qdrant."""
    logger.info(f"Starting ingestion for document {document_id} ({filename})")
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc is None:
                logger.error(f"Document {document_id} not found")
                return
            doc.status = "processing"
            await db.commit()
            logger.info(f"Document {document_id} status set to 'processing'")

            text = load_text(file_path)
            if not text.strip():
                doc.status = "failed"
                doc.error_message = "文件内容为空"
                await db.commit()
                return

            chunks = chunk_text(text)
            if not chunks:
                doc.status = "failed"
                doc.error_message = "分块后无有效内容"
                await db.commit()
                return

            kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
            kb = kb_result.scalar_one_or_none()
            if kb is None:
                doc.status = "failed"
                doc.error_message = "知识库不存在"
                await db.commit()
                return

            embedding_model = kb.embedding_model or settings.DEFAULT_EMBEDDING_MODEL

            # Per-KB API key → global ApiKey
            api_key = kb.embedding_api_key
            base_url = kb.embedding_base_url
            if not api_key:
                key_result = await db.execute(
                    select(ApiKey).where(
                        ApiKey.user_id == kb.user_id,
                        ApiKey.provider == "embedding",
                        ApiKey.is_active == True,
                    )
                )
                api_key_obj = key_result.scalar_one_or_none()
                if api_key_obj and api_key_obj.api_key:
                    api_key = api_key_obj.api_key
                    base_url = api_key_obj.base_url
            if not api_key or api_key == "xxx":
                doc.status = "failed"
                doc.error_message = "未配置 Embedding API Key，请在知识库设置或模型配置中设置"
                await db.commit()
                return

            client = await get_embedding_client(api_key, base_url)
            embeddings = await embed_texts(client, chunks, model=embedding_model)

            dimension = len(embeddings[0]) if embeddings else 1536

            qdrant = get_qdrant_client()
            col = ensure_collection(qdrant, kb_id, dimension=dimension)

            point_ids = []
            points = []
            for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "text": chunk,
                            "document_id": str(document_id),
                            "chunk_index": i,
                            "filename": filename,
                        },
                    )
                )

            upsert_points(qdrant, col, points)

            doc.status = "completed"
            doc.chunk_count = len(chunks)
            doc.qdrant_point_ids = [uuid.UUID(pid) for pid in point_ids]
            await db.commit()

            total_chunks = await db.scalar(
                select(func.coalesce(func.sum(Document.chunk_count), 0))
                .where(Document.kb_id == kb_id, Document.status == "completed")
            )
            kb.chunk_count = total_chunks or 0
            await db.commit()

            logger.info(f"Document {document_id} ingested: {len(chunks)} chunks")

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Ingestion failed for document {document_id}: {e}\n{tb}")
            try:
                async with async_session_factory() as error_db:
                    result = await error_db.execute(
                        select(Document).where(Document.id == document_id)
                    )
                    doc = result.scalar_one_or_none()
                    if doc:
                        doc.status = "failed"
                        doc.error_message = str(e)[:500]
                        await error_db.commit()
                        logger.info(f"Document {document_id} status set to 'failed'")
            except Exception as inner_e:
                logger.error(f"Failed to update document error status: {inner_e}")


async def delete_document_vectors(
    kb_id: uuid.UUID, point_ids: list[uuid.UUID]
) -> None:
    """Remove a document's vectors from Qdrant."""
    from app.rag.vector_store import collection_name as cn

    qdrant = get_qdrant_client()
    col = cn(kb_id)
    delete_points_by_ids(qdrant, col, [str(pid) for pid in point_ids])


async def delete_kb_collection(kb_id: uuid.UUID) -> None:
    """Delete the entire Qdrant collection for a KB."""
    qdrant = get_qdrant_client()
    delete_collection(qdrant, kb_id)
