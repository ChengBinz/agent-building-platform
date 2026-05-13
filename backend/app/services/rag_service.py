"""RAG context retrieval and embedding key resolution."""
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.api_key import ApiKey
from app.models.conversation import Conversation
from app.models.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_embedding_key(
        self, user_id: uuid.UUID
    ) -> tuple[str, str | None] | None:
        """Resolve embedding API key for a user.

        Lookup order:
          1. Default embedding model (DefaultModel)
          2. Any active embedding model (LLMModel)
          3. Legacy api_keys table (provider='embedding')

        Returns (api_key, base_url) or None.
        """
        from app.models.llm_model import DefaultModel, LLMModel

        # 1) Default embedding model
        dres = await self.db.execute(
            select(DefaultModel).where(
                DefaultModel.user_id == user_id,
                DefaultModel.model_type == "embedding",
            )
        )
        d = dres.scalar_one_or_none()
        if d is not None:
            llm = await self.db.get(LLMModel, d.llm_model_id)
            if llm and llm.api_key:
                return llm.api_key, llm.base_url

        # 2) Any active embedding model
        eres = await self.db.execute(
            select(LLMModel).where(
                LLMModel.user_id == user_id,
                LLMModel.model_type == "embedding",
                LLMModel.is_active == True,
            ).order_by(LLMModel.created_at.desc())
        )
        llm = eres.scalars().first()
        if llm and llm.api_key:
            return llm.api_key, llm.base_url

        # 3) Legacy api_keys
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.user_id == user_id,
                ApiKey.provider == "embedding",
                ApiKey.is_active == True,
            )
        )
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj and api_key_obj.api_key:
            return api_key_obj.api_key, api_key_obj.base_url

        return None

    async def retrieve_context(
        self, conv: Conversation, query: str
    ) -> str | None:
        """Retrieve relevant chunks from KBs and format as context string."""
        if not conv.kb_ids:
            return None

        try:
            from app.rag.embedder import embed_query, get_embedding_client
            from app.rag.vector_store import (
                collection_name,
                get_qdrant_client,
                search,
            )

            # Load all KBs
            kb_result = await self.db.execute(
                select(KnowledgeBase).where(KnowledgeBase.id.in_(conv.kb_ids))
            )
            kbs = kb_result.scalars().all()
            if not kbs:
                return None

            # Resolve global embedding key
            global_key, global_url = await self.resolve_embedding_key(
                conv.user_id
            ) or (None, None)

            # Group KBs by (api_key, base_url, model)
            groups: dict[tuple, list] = {}
            for kb in kbs:
                key = kb.embedding_api_key or global_key
                url = (
                    kb.embedding_base_url
                    or global_url
                    or settings.EMBEDDING_BASE_URL
                )
                model = kb.embedding_model or settings.DEFAULT_EMBEDDING_MODEL
                if not key or key == "xxx":
                    continue
                group_key = (key, url or "", model)
                groups.setdefault(group_key, []).append(kb)

            if not groups:
                return None

            qdrant = get_qdrant_client()
            all_chunks: list[dict] = []

            for (key, url, model), kb_group in groups.items():
                client = await get_embedding_client(key, url or None)
                query_vector = await embed_query(client, query, model=model)

                for kb in kb_group:
                    col = collection_name(kb.id)
                    try:
                        results = search(qdrant, col, query_vector)
                        for r in results:
                            r["kb_id"] = str(kb.id)
                        all_chunks.extend(results)
                    except Exception:
                        continue

            if not all_chunks:
                return None

            all_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
            chunks = all_chunks[: settings.RETRIEVAL_TOP_K]

            if not chunks:
                return None

            context_parts = []
            for i, chunk in enumerate(chunks, 1):
                source = chunk.get("filename", "unknown")
                text = chunk.get("text", "")
                context_parts.append(f"[{i}] (来源: {source})\n{text}")

            return (
                "以下是与用户问题相关的知识库内容，请基于这些内容回答问题：\n\n"
                + "\n\n".join(context_parts)
            )

        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return None
