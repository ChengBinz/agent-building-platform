"""Conversation CRUD and message handling with real LLM calls."""
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.engine.registry import get_provider
from app.models.agent import Agent
from app.models.api_key import ApiKey
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    SendMessageRequest,
    SendMessageResponse,
)

logger = logging.getLogger(__name__)


# Maps the provider key used in Conversation/Agent (lowercase) to the list of
# factory names that may store its credentials in the llm_models table.
_FACTORY_ALIASES: dict[str, list[str]] = {
    "openai": ["OpenAI", "OpenAI-API-Compatible"],
    "anthropic": ["Anthropic"],
    "deepseek": ["DeepSeek"],
    "dashscope": ["Tongyi-Qianwen"],
    "tongyi": ["Tongyi-Qianwen"],
    "zhipu": ["ZHIPU-AI"],
    "moonshot": ["Moonshot"],
    "xai": ["xAI"],
    "gemini": ["Gemini"],
    "mistral": ["Mistral"],
    "azure": ["Azure-OpenAI"],
    "ollama": ["Ollama"],
    "vllm": ["VLLM"],
    "siliconflow": ["SILICONFLOW"],
    "gitee": ["GiteeAI"],
    "groq": ["Groq"],
    "openrouter": ["OpenRouter"],
    "hunyuan": ["Tencent-Hunyuan"],
    "minimax": ["MiniMax"],
    "baichuan": ["BaiChuan"],
}


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_conversations(self, user_id: uuid.UUID, agent_id: uuid.UUID | None = None) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        if agent_id:
            stmt = stmt.where(Conversation.agent_id == agent_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_conversation(
        self, user_id: uuid.UUID, data: ConversationCreate
    ) -> Conversation:
        model_name = data.model_name
        provider = data.provider
        system_prompt = data.system_prompt
        kb_ids = None

        if data.agent_id:
            result = await self.db.execute(
                select(Agent).where(Agent.id == data.agent_id, Agent.user_id == user_id)
            )
            agent = result.scalar_one_or_none()
            if agent is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="智能体不存在")
            model_name = model_name or agent.model_name
            provider = provider or agent.provider
            system_prompt = system_prompt or agent.system_prompt
            kb_ids = agent.kb_ids

        conv = Conversation(
            user_id=user_id,
            agent_id=data.agent_id,
            title=data.title,
            model_name=model_name,
            provider=provider,
            system_prompt=system_prompt,
            kb_ids=kb_ids,
        )
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    async def get_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Conversation:
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
        return conv

    async def update_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, data
    ) -> Conversation:
        conv = await self.get_conversation(user_id, conversation_id)
        if data.title is not None:
            conv.title = data.title
        if data.model_name is not None:
            conv.model_name = data.model_name
        if data.provider is not None:
            conv.provider = data.provider
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    async def delete_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> None:
        conv = await self.get_conversation(user_id, conversation_id)
        await self.db.delete(conv)
        await self.db.flush()

    async def _get_api_key(self, user_id: uuid.UUID, provider: str) -> tuple[str, str]:
        """Return (api_key, base_url) for the user + provider.

        Lookup order:
          1. llm_models table (new RAGFlow-style) — match by factory name OR model family
          2. api_keys table (legacy) — match by provider key
        """
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="对话未指定模型提供商",
            )

        # 1) new llm_models lookup (factory name match; case-insensitive via aliases)
        from app.models.llm_model import LLMModel

        factory_aliases = _FACTORY_ALIASES.get(provider.lower(), [provider])
        result = await self.db.execute(
            select(LLMModel).where(
                LLMModel.user_id == user_id,
                LLMModel.factory.in_(factory_aliases),
                LLMModel.is_active == True,
            ).order_by(LLMModel.created_at.desc())
        )
        llm = result.scalars().first()
        if llm and llm.api_key:
            return llm.api_key, llm.base_url or ""

        # 2) legacy api_keys lookup
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.user_id == user_id,
                ApiKey.provider == provider,
                ApiKey.is_active == True,
            )
        )
        key = result.scalar_one_or_none()
        if not key or not key.api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"请先在模型配置中为 {provider} 添加可用的模型与 API Key",
            )
        return key.api_key, key.base_url or ""

    async def send_message(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, data: SendMessageRequest
    ) -> SendMessageResponse:
        conv = await self.get_conversation(user_id, conversation_id)

        # Save user message
        now = datetime.now(timezone.utc)
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=data.content,
            created_at=now,
            updated_at=now,
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Build message history
        messages = await self._build_messages(conv, data.content)

        # Get API key and call LLM
        api_key, base_url = await self._get_api_key(user_id, conv.provider)
        provider = get_provider(conv.provider, api_key, base_url)

        full_response = ""
        full_thinking = ""
        async for chunk in provider.generate_stream(messages, conv.model_name):
            if chunk.get("reasoning"):
                full_thinking += chunk["reasoning"]
            full_response += chunk["token"]

        if not full_response and not full_thinking:
            full_response = "(模型返回了空回复)"

        # Save assistant reply
        now2 = datetime.now(timezone.utc)
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_response,
            thinking_content=full_thinking or None,
            token_count=(len(full_response) + len(full_thinking)) // 2,
            created_at=now2,
            updated_at=now2,
        )
        self.db.add(assistant_msg)

        # Update conversation counters
        conv.message_count = (
            await self.db.scalar(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conv.id
                )
            )
            or 0
        )
        conv.total_tokens = (
            await self.db.scalar(
                select(func.coalesce(func.sum(Message.token_count), 0)).where(
                    Message.conversation_id == conv.id
                )
            )
            or 0
        )

        await self.db.flush()
        return SendMessageResponse(role="assistant", content=full_response)

    async def send_message_stream(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, data: SendMessageRequest
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response via SSE. Yields SSE-formatted strings."""
        conv = await self.get_conversation(user_id, conversation_id)

        # Save user message
        now = datetime.now(timezone.utc)
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=data.content,
            created_at=now,
            updated_at=now,
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Build message history
        messages = await self._build_messages(conv, data.content)

        # Get API key and call LLM
        api_key, base_url = await self._get_api_key(user_id, conv.provider)
        provider = get_provider(conv.provider, api_key, base_url)

        full_response = ""
        full_thinking = ""
        in_thinking = False
        try:
            async for chunk in provider.generate_stream(messages, conv.model_name):
                reasoning = chunk.get("reasoning")
                token = chunk.get("token", "")

                if reasoning:
                    if not in_thinking:
                        yield "data: [THINKING]\n\n"
                        in_thinking = True
                    full_thinking += reasoning
                    yield f"data: {reasoning}\n\n"
                if token:
                    if in_thinking:
                        yield "data: [/THINKING]\n\n"
                        in_thinking = False
                    full_response += token
                    yield f"data: {token}\n\n"
        except Exception as e:
            if in_thinking:
                yield "data: [/THINKING]\n\n"
            error_msg = f"LLM 调用失败: {str(e)}"
            yield f"data: {error_msg}\n\n"

        if in_thinking:
            yield "data: [/THINKING]\n\n"

        if not full_response and not full_thinking:
            full_response = "(模型返回了空回复)"

        # Save assistant reply
        now2 = datetime.now(timezone.utc)
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_response,
            thinking_content=full_thinking or None,
            token_count=(len(full_response) + len(full_thinking)) // 2,
            created_at=now2,
            updated_at=now2,
        )
        self.db.add(assistant_msg)

        # Update counters
        conv.message_count = (
            await self.db.scalar(
                select(func.count(Message.id)).where(
                    Message.conversation_id == conv.id
                )
            )
            or 0
        )
        conv.total_tokens = (
            await self.db.scalar(
                select(func.coalesce(func.sum(Message.token_count), 0)).where(
                    Message.conversation_id == conv.id
                )
            )
            or 0
        )
        await self.db.flush()

        yield "data: [DONE]\n\n"

    async def _build_messages(self, conv: Conversation, current_content: str) -> list[dict]:
        """Build LLM message list: system prompt + RAG context + history."""
        messages: list[dict] = []
        if conv.system_prompt:
            messages.append({"role": "system", "content": conv.system_prompt})

        # RAG context injection
        if conv.kb_ids:
            rag_context = await self._retrieve_rag_context(conv, current_content)
            if rag_context:
                messages.append({"role": "system", "content": rag_context})

        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
        )
        for msg in result.scalars().all():
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    async def _retrieve_rag_context(self, conv: Conversation, query: str) -> str | None:
        """Retrieve relevant chunks from KBs and format as context string."""
        if not conv.kb_ids:
            return None

        try:
            from app.models.knowledge_base import KnowledgeBase
            from app.rag.embedder import get_embedding_client, embed_query
            from app.rag.vector_store import collection_name, get_qdrant_client, search

            # Load all KBs and group by embedding config
            kb_result = await self.db.execute(
                select(KnowledgeBase).where(KnowledgeBase.id.in_(conv.kb_ids))
            )
            kbs = kb_result.scalars().all()
            if not kbs:
                return None

            # Fallback: get global embedding provider key
            # Priority: llm_models (model_type=embedding) > legacy api_keys('embedding')
            global_key = None
            global_url = None

            from app.models.llm_model import LLMModel, DefaultModel

            # Prefer the user's default embedding model
            dres = await self.db.execute(
                select(DefaultModel).where(
                    DefaultModel.user_id == conv.user_id,
                    DefaultModel.model_type == "embedding",
                )
            )
            d = dres.scalar_one_or_none()
            if d is not None:
                llm = await self.db.get(LLMModel, d.llm_model_id)
                if llm and llm.api_key:
                    global_key = llm.api_key
                    global_url = llm.base_url
            if not global_key:
                # any active embedding model the user has
                eres = await self.db.execute(
                    select(LLMModel).where(
                        LLMModel.user_id == conv.user_id,
                        LLMModel.model_type == "embedding",
                        LLMModel.is_active == True,
                    ).order_by(LLMModel.created_at.desc())
                )
                llm = eres.scalars().first()
                if llm and llm.api_key:
                    global_key = llm.api_key
                    global_url = llm.base_url
            if not global_key:
                # legacy: api_keys row with provider='embedding'
                result = await self.db.execute(
                    select(ApiKey).where(
                        ApiKey.user_id == conv.user_id,
                        ApiKey.provider == "embedding",
                        ApiKey.is_active == True,
                    )
                )
                api_key_obj = result.scalar_one_or_none()
                if api_key_obj and api_key_obj.api_key:
                    global_key = api_key_obj.api_key
                    global_url = api_key_obj.base_url

            # Group KBs by (api_key, base_url, model)
            groups: dict[tuple, list] = {}
            for kb in kbs:
                key = kb.embedding_api_key or global_key
                url = kb.embedding_base_url or global_url or settings.EMBEDDING_BASE_URL
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
