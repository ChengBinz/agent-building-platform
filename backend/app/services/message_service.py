"""Message sending (stream/non-stream), LLM provider resolution, message history building."""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.registry import get_provider
from app.models.api_key import ApiKey
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import SendMessageRequest, SendMessageResponse
from app.services import tool_service
from app.services.conversation_service import ConversationService
from app.services.rag_service import RAGService

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

MAX_TOOL_ROUNDS = 5


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._conv_service = ConversationService(db)
        self._rag_service = RAGService(db)

    async def send_message(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        data: SendMessageRequest,
    ) -> SendMessageResponse:
        conv = await self._conv_service.get_conversation(user_id, conversation_id)

        await self._save_user_message(conv, data.content)
        messages = await self._build_messages(conv, data.content)

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

        await self._save_assistant_response(conv, full_response, full_thinking, [])
        await self._update_conversation_counters(conv)

        return SendMessageResponse(role="assistant", content=full_response)

    async def send_message_stream(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        data: SendMessageRequest,
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response via SSE. Yields SSE-formatted strings."""
        conv = await self._conv_service.get_conversation(user_id, conversation_id)

        await self._save_user_message(conv, data.content)
        messages = await self._build_messages(conv, data.content)

        api_key, base_url = await self._get_api_key(user_id, conv.provider)
        provider = get_provider(conv.provider, api_key, base_url)

        # Load agent tools
        agent_tool_names: list[str] = []
        if conv.agent and conv.agent.tools:
            agent_tool_names = conv.agent.tools
        tool_schemas = (
            await tool_service.get_tool_schemas(agent_tool_names, user_id, self.db)
            if agent_tool_names
            else []
        )

        full_response = ""
        full_thinking = ""
        in_thinking = False
        tool_call_messages: list[dict] = []

        try:
            # ── LLM call loop with tool calling ──
            for round_idx in range(MAX_TOOL_ROUNDS + 1):
                collected_tool_calls: list[dict] = []
                round_response = ""

                stream_kwargs = {}
                if tool_schemas:
                    stream_kwargs["tools"] = tool_schemas
                    stream_kwargs["tool_choice"] = "auto"

                logger.info(
                    f"[Tool Loop] Round {round_idx}, messages count: {len(messages)}"
                )

                async for chunk in provider.generate_stream(
                    messages, conv.model_name, **stream_kwargs
                ):
                    reasoning = chunk.get("reasoning")
                    token = chunk.get("token", "")
                    tool_calls = chunk.get("tool_calls")

                    if tool_calls:
                        collected_tool_calls = tool_calls
                        logger.info(
                            f"[Tool Loop] Received {len(tool_calls)} tool calls"
                        )
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
                        round_response += token
                        full_response += token
                        yield f"data: {token}\n\n"

                # If no tool calls, we're done
                if not collected_tool_calls:
                    break

                # Close any open thinking before tool call markers
                if in_thinking:
                    yield "data: [/THINKING]\n\n"
                    in_thinking = False

                # ── Execute tool calls ──
                assistant_tc_msg = {
                    "role": "assistant",
                    "content": round_response or None,
                    "tool_calls": collected_tool_calls,
                }
                messages.append(assistant_tc_msg)
                tool_call_messages.append(assistant_tc_msg)

                for tc_idx, tc in enumerate(collected_tool_calls):
                    func_name = tc["function"]["name"]
                    try:
                        func_args = json.loads(tc["function"]["arguments"])
                    except (json.JSONDecodeError, TypeError):
                        func_args = {}

                    logger.info(
                        f"[Tool Loop] Executing tool {tc_idx + 1}/{len(collected_tool_calls)}: {func_name}"
                    )

                    yield f'data: [TOOL_CALL]{json.dumps({"name": func_name, "args": func_args}, ensure_ascii=False)}\n\n'

                    tool_result = await tool_service.execute_tool(
                        func_name, func_args, user_id, self.db
                    )

                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_result,
                    }
                    messages.append(tool_msg)
                    tool_call_messages.append(tool_msg)

                    yield f'data: [TOOL_RESULT]{json.dumps({"name": func_name, "result": tool_result}, ensure_ascii=False)}\n\n'

        except Exception as e:
            if in_thinking:
                yield "data: [/THINKING]\n\n"
            yield f"data: LLM 调用失败: {str(e)}\n\n"

        if in_thinking:
            yield "data: [/THINKING]\n\n"

        if not full_response and not full_thinking:
            full_response = "(模型返回了空回复)"
            yield f"data: {full_response}\n\n"

        await self._save_assistant_response(
            conv, full_response, full_thinking, tool_call_messages
        )
        await self._update_conversation_counters(conv)

        yield "data: [DONE]\n\n"

    async def _get_api_key(
        self, user_id: uuid.UUID, provider: str
    ) -> tuple[str, str]:
        """Return (api_key, base_url) for the user + provider."""
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="对话未指定模型提供商",
            )

        from app.models.llm_model import LLMModel

        factory_aliases = _FACTORY_ALIASES.get(provider.lower(), [provider])
        result = await self.db.execute(
            select(LLMModel)
            .where(
                LLMModel.user_id == user_id,
                LLMModel.factory.in_(factory_aliases),
                LLMModel.is_active == True,
            )
            .order_by(LLMModel.created_at.desc())
        )
        llm = result.scalars().first()
        if llm and llm.api_key:
            return llm.api_key, llm.base_url or ""

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

    async def _build_messages(
        self, conv: Conversation, current_content: str
    ) -> list[dict]:
        """Build LLM message list: system prompt + RAG context + history."""
        messages: list[dict] = []
        if conv.system_prompt:
            messages.append({"role": "system", "content": conv.system_prompt})

        # RAG context injection
        if conv.kb_ids:
            rag_context = await self._rag_service.retrieve_context(
                conv, current_content
            )
            if rag_context:
                messages.append({"role": "system", "content": rag_context})

        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
        )
        for msg in result.scalars().all():
            entry = {"role": msg.role, "content": msg.content}
            if msg.role == "assistant" and msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc.get("arguments", "{}"),
                        },
                    }
                    for tc in msg.tool_calls
                    if "id" in tc
                ]
            if msg.role == "tool" and msg.tool_calls:
                tc_id = msg.tool_calls[0].get("id") if msg.tool_calls else None
                if tc_id:
                    entry["tool_call_id"] = tc_id
            messages.append(entry)

        return messages

    async def _save_user_message(
        self, conv: Conversation, content: str
    ) -> None:
        now = datetime.now(timezone.utc)
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=content,
            created_at=now,
            updated_at=now,
        )
        self.db.add(user_msg)
        await self.db.flush()

    async def _save_assistant_response(
        self,
        conv: Conversation,
        full_response: str,
        full_thinking: str,
        tool_call_messages: list[dict],
    ) -> None:
        now = datetime.now(timezone.utc)

        if tool_call_messages:
            for tm in tool_call_messages:
                if tm.get("role") == "assistant" and tm.get("tool_calls"):
                    tool_calls_data = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"],
                            },
                        }
                        for tc in tm["tool_calls"]
                    ]
                    asst_msg = Message(
                        conversation_id=conv.id,
                        role="assistant",
                        content=tm.get("content"),
                        tool_calls=tool_calls_data,
                        token_count=len(tm.get("content") or "") // 2,
                        created_at=now,
                        updated_at=now,
                    )
                    self.db.add(asst_msg)
                elif tm.get("role") == "tool":
                    tool_db_msg = Message(
                        conversation_id=conv.id,
                        role="tool",
                        content=tm["content"],
                        tool_calls=[{"id": tm["tool_call_id"]}],
                        created_at=now,
                        updated_at=now,
                    )
                    self.db.add(tool_db_msg)

        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_response,
            thinking_content=full_thinking or None,
            token_count=(len(full_response) + len(full_thinking)) // 2,
            created_at=now,
            updated_at=now,
        )
        self.db.add(assistant_msg)

    async def _update_conversation_counters(self, conv: Conversation) -> None:
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
