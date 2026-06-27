"""Message sending (stream/non-stream), LLM provider resolution, message history building."""
import asyncio
import json
import logging
import time
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
from app.models.usage_log import UsageLog
from app.schemas.chat import SendMessageRequest, SendMessageResponse
from app.services import tool_service
from app.services import memory_service
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

# 调用 LLM 时最多保留多少条最近的对话历史（更早的会被摘要替代）
HISTORY_WINDOW = 10

# 摘要后台任务防 GC
_summary_background_tasks: set[asyncio.Task] = set()


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
        usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        start_ts = time.time()
        log_status = "success"
        log_error: str | None = None

        try:
            async for chunk in provider.generate_stream(messages, conv.model_name):
                if chunk.get("reasoning"):
                    full_thinking += chunk["reasoning"]
                full_response += chunk.get("token", "")
                chunk_usage = chunk.get("usage")
                if chunk_usage:
                    usage_total["prompt_tokens"] += chunk_usage.get("prompt_tokens", 0) or 0
                    usage_total["completion_tokens"] += chunk_usage.get("completion_tokens", 0) or 0
                    usage_total["total_tokens"] += chunk_usage.get("total_tokens", 0) or 0
        except Exception as e:
            log_status = "failed"
            log_error = str(e)[:500]
            raise
        finally:
            if not full_response and not full_thinking and log_status == "success":
                full_response = "(模型返回了空回复)"

            await self._save_assistant_response(conv, full_response, full_thinking, [])
            await self._record_usage(
                user_id=user_id,
                conv=conv,
                usage=usage_total,
                fallback_text=full_response + full_thinking,
                start_ts=start_ts,
                status_=log_status,
                error_message=log_error,
            )
            await self._update_conversation_counters(conv)

        # —— 触发后台摘要任务（不阻塞响应） ——
        self._schedule_summary_task(user_id, conv, api_key, base_url)

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

        # 在进入真正的 SSE 流之前先校验 API Key，失败时以 SSE 错误事件返回，
        # 避免响应头已发出后再抛 HTTPException 导致前端只看到 "network error"
        try:
            api_key, base_url = await self._get_api_key(user_id, conv.provider)
        except HTTPException as e:
            detail = e.detail if isinstance(e.detail, str) else str(e.detail)
            yield f"data: ❌ {detail}\n\n"
            yield "data: [DONE]\n\n"
            return

        provider = get_provider(conv.provider, api_key, base_url)

        # Load agent tools
        agent_tool_names: list[str] = []
        if conv.agent and conv.agent.tools:
            agent_tool_names = list(conv.agent.tools)

        # 用户在本轮对话开启了「联网搜索」时，动态把搜索类工具临时加入工具列表
        if data.enable_web_search:
            extra = await tool_service.find_web_search_tools(user_id, self.db)
            for name in extra:
                if name not in agent_tool_names:
                    agent_tool_names.append(name)

        tool_schemas = (
            await tool_service.get_tool_schemas(agent_tool_names, user_id, self.db)
            if agent_tool_names
            else []
        )

        full_response = ""
        full_thinking = ""
        in_thinking = False
        tool_call_messages: list[dict] = []

        # —— Token 用量统计 ——
        usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        start_ts = time.time()
        log_status = "success"
        log_error: str | None = None

        try:
            # ── LLM call loop with tool calling ──
            for round_idx in range(MAX_TOOL_ROUNDS + 1):
                collected_tool_calls: list[dict] = []
                round_response = ""

                stream_kwargs = {}
                if tool_schemas:
                    stream_kwargs["tools"] = tool_schemas
                    # 最后一轮强制 LLM 给出文本回复，避免继续调用工具但被强制截断
                    stream_kwargs["tool_choice"] = (
                        "none" if round_idx >= MAX_TOOL_ROUNDS else "auto"
                    )

                logger.info(
                    f"[Tool Loop] Round {round_idx}, messages count: {len(messages)}"
                )

                async for chunk in provider.generate_stream(
                    messages, conv.model_name, **stream_kwargs
                ):
                    reasoning = chunk.get("reasoning")
                    token = chunk.get("token", "")
                    tool_calls = chunk.get("tool_calls")
                    chunk_usage = chunk.get("usage")

                    if chunk_usage:
                        usage_total["prompt_tokens"] += chunk_usage.get("prompt_tokens", 0) or 0
                        usage_total["completion_tokens"] += chunk_usage.get("completion_tokens", 0) or 0
                        usage_total["total_tokens"] += chunk_usage.get("total_tokens", 0) or 0

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
            log_status = "failed"
            log_error = str(e)[:500]
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

        # 写入 token 用量日志
        await self._record_usage(
            user_id=user_id,
            conv=conv,
            usage=usage_total,
            fallback_text=full_response + full_thinking,
            start_ts=start_ts,
            status_=log_status,
            error_message=log_error,
        )

        await self._update_conversation_counters(conv)

        # —— 触发后台摘要任务（不阻塞响应） ——
        self._schedule_summary_task(user_id, conv, api_key, base_url)

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
        """Build LLM message list: system prompt + memory summary + RAG context + history."""
        messages: list[dict] = []
        if conv.system_prompt:
            messages.append({"role": "system", "content": conv.system_prompt})

        # —— 对话记忆摘要注入（如有） ——
        summary, summarized_up_to = await memory_service.get_summary(
            self.db, conv.id
        )
        if summary:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "以下是该对话此前内容的摘要，请把它当作背景：\n" + summary
                    ),
                }
            )

        # RAG context injection
        if conv.kb_ids:
            rag_context = await self._rag_service.retrieve_context(
                conv, current_content
            )
            if rag_context:
                messages.append({"role": "system", "content": rag_context})

        # —— 只取最近 HISTORY_WINDOW 条历史（如果已有摘要，则跳过已摘要的部分） ——
        # 优先级：if has summary → 取摘要点之后的所有；否则 → 取最近 HISTORY_WINDOW 条
        if summary and summarized_up_to > 0:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at.asc())
                .offset(summarized_up_to)
            )
        else:
            # 取最近 N 条（用子查询反转排序拿最后 N 条，再正向排好）
            stmt = (
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc())
                .limit(HISTORY_WINDOW)
            )

        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())
        if not (summary and summarized_up_to > 0):
            rows.reverse()  # 反转回正序

        for msg in rows:
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
                        # 仅有 tool_calls 而无文字时 content 为空字符串而非 NULL
                        content=tm.get("content") or "",
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
                        content=tm.get("content") or "",
                        tool_calls=[{"id": tm["tool_call_id"]}],
                        created_at=now,
                        updated_at=now,
                    )
                    self.db.add(tool_db_msg)

        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_response or "",
            thinking_content=full_thinking or None,
            token_count=(len(full_response) + len(full_thinking)) // 2,
            created_at=now,
            updated_at=now,
        )
        self.db.add(assistant_msg)
        # 提前 flush，让消息写入错误立即暴露而不是被后续 _record_usage 的 try/except 误吞
        await self.db.flush()

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

    def _schedule_summary_task(
        self,
        user_id: uuid.UUID,
        conv: Conversation,
        api_key: str,
        base_url: str,
    ) -> None:
        """非阻塞地触发后台摘要任务，幂等。"""
        if not conv or not conv.model_name or not api_key:
            return
        try:
            task = asyncio.create_task(
                memory_service.check_and_summarize_async(
                    conversation_id=conv.id,
                    api_key=api_key,
                    base_url=base_url or "",
                    provider=conv.provider or "",
                    model=conv.model_name,
                )
            )
            _summary_background_tasks.add(task)
            task.add_done_callback(_summary_background_tasks.discard)
        except Exception as e:
            logger.warning(f"Failed to schedule summary task: {e}")

    async def _record_usage(
        self,
        *,
        user_id: uuid.UUID,
        conv: Conversation,
        usage: dict,
        fallback_text: str,
        start_ts: float,
        status_: str,
        error_message: str | None,
    ) -> None:
        """落库一条 token 用量日志。优先用 provider 返回的真实 usage，
        拿不到时用 tiktoken 本地估算。"""
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or 0)

        if total_tokens == 0:
            # 兜底：tiktoken 估算 completion，prompt 留 0
            completion_tokens = _estimate_tokens(fallback_text)
            total_tokens = completion_tokens

        try:
            self.db.add(
                UsageLog(
                    user_id=user_id,
                    conversation_id=conv.id,
                    model_name=conv.model_name or "unknown",
                    provider=conv.provider or "unknown",
                    request_type="chat",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=int((time.time() - start_ts) * 1000),
                    status=status_,
                    error_message=error_message,
                )
            )
            await self.db.flush()
        except Exception as e:
            # 日志写入失败不影响主流程
            logger.warning(f"Failed to write UsageLog: {e}")


# ── Token estimation fallback ────────────────────────────────────────

_TIKTOKEN_ENC = None


def _estimate_tokens(text: str) -> int:
    """优先用 tiktoken 估算，不可用时回退到字符数粗估。"""
    if not text:
        return 0
    global _TIKTOKEN_ENC
    if _TIKTOKEN_ENC is None:
        try:
            import tiktoken
            _TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _TIKTOKEN_ENC = False  # 标记不可用，避免重复 import
    if _TIKTOKEN_ENC and _TIKTOKEN_ENC is not False:
        try:
            return len(_TIKTOKEN_ENC.encode(text))
        except Exception:
            pass
    # 粗估：中文/英文混合大约 1.5 字符/token
    return max(1, len(text) * 2 // 3)
