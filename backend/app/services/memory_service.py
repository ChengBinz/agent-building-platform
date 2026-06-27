"""Conversation memory service.

每对话维护一份 LLM 生成的「滚动摘要」，在长对话中替代被裁掉的早期消息，
让上下文窗口保持稳定。

设计：
- 每 N 条消息（默认 10）触发一次摘要
- 增量摘要：把上一次 summary + 新增的一批消息送给 LLM，得到新 summary
- 摘要存 PostgreSQL（持久化）+ Redis（7 天缓存）

公开接口：
- get_summary(conv_id)        读取摘要（先 Redis 再 DB）
- check_and_summarize(...)    后台触发，幂等
"""
import logging
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import redis_get, redis_set
from app.db.session import async_session_factory
from app.engine.registry import get_provider
from app.models.conversation import Conversation
from app.models.conversation_memory import ConversationMemory
from app.models.message import Message

logger = logging.getLogger(__name__)

# 每多少条消息触发一次摘要
SUMMARY_TRIGGER_INTERVAL = 10
# 保留最近多少条消息（不会被摘要替换）
RECENT_MESSAGE_WINDOW = 10
# 摘要在 Redis 的 TTL
REDIS_TTL_SECONDS = 7 * 24 * 3600


def _cache_key(conv_id: uuid.UUID) -> str:
    return f"conversation_memory:{conv_id}"


async def get_summary(
    db: AsyncSession, conv_id: uuid.UUID
) -> tuple[Optional[str], int]:
    """返回 (summary_text, summarized_up_to)。

    优先读 Redis；未命中则查 DB 并写回 Redis。
    """
    cached = await redis_get(_cache_key(conv_id))
    if cached is not None:
        # 缓存格式：'<count>|<summary>'
        try:
            head, body = cached.split("|", 1)
            return body or None, int(head or 0)
        except ValueError:
            pass  # 格式异常，降级走 DB

    result = await db.execute(
        select(ConversationMemory).where(
            ConversationMemory.conversation_id == conv_id
        )
    )
    mem = result.scalar_one_or_none()
    if mem is None:
        return None, 0

    if mem.summary:
        await redis_set(
            _cache_key(conv_id),
            f"{mem.summarized_up_to}|{mem.summary}",
            ex=REDIS_TTL_SECONDS,
        )
    return mem.summary, mem.summarized_up_to


async def _save_summary(
    db: AsyncSession,
    conv_id: uuid.UUID,
    summary: str,
    summarized_up_to: int,
) -> None:
    result = await db.execute(
        select(ConversationMemory).where(
            ConversationMemory.conversation_id == conv_id
        )
    )
    mem = result.scalar_one_or_none()
    if mem is None:
        mem = ConversationMemory(
            conversation_id=conv_id,
            summary=summary,
            summarized_up_to=summarized_up_to,
        )
        db.add(mem)
    else:
        mem.summary = summary
        mem.summarized_up_to = summarized_up_to
    await db.flush()
    await redis_set(
        _cache_key(conv_id),
        f"{summarized_up_to}|{summary}",
        ex=REDIS_TTL_SECONDS,
    )


def _format_messages_for_summary(messages: list[Message]) -> str:
    """把消息列表渲染为给摘要模型的输入文本。"""
    lines: list[str] = []
    for m in messages:
        role = {"user": "用户", "assistant": "助手", "tool": "工具"}.get(m.role, m.role)
        content = (m.content or "").strip()
        if not content:
            continue
        # 截断过长的工具结果
        if len(content) > 800:
            content = content[:800] + "...(已截断)"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


async def _llm_summarize(
    api_key: str,
    base_url: str,
    provider: str,
    model: str,
    previous_summary: Optional[str],
    new_messages_text: str,
) -> str:
    """调用 LLM 生成增量摘要。出错时抛异常，由调用方决定如何处理。"""
    prompt_parts: list[str] = []
    if previous_summary:
        prompt_parts.append(
            f"以下是该对话已有的摘要：\n{previous_summary}\n"
        )
    prompt_parts.append(
        "以下是该对话新增的消息：\n"
        f"{new_messages_text}\n\n"
        "请基于以上信息生成一份更新后的对话摘要，要求：\n"
        "1. 用中文，控制在 400 字以内；\n"
        "2. 保留关键事实、用户偏好、未解决的问题；\n"
        "3. 不要使用列表/标题，写成连贯段落；\n"
        "4. 直接输出摘要内容，不要加任何前缀。"
    )

    llm = get_provider(provider, api_key, base_url)
    summary_chunks: list[str] = []
    async for chunk in llm.generate_stream(
        [{"role": "user", "content": "\n".join(prompt_parts)}],
        model,
    ):
        token = chunk.get("token", "")
        if token:
            summary_chunks.append(token)
    return "".join(summary_chunks).strip()


async def check_and_summarize_async(
    conversation_id: uuid.UUID,
    api_key: str,
    base_url: str,
    provider: str,
    model: str,
) -> None:
    """后台任务：检查并按需触发摘要。使用独立 DB session。

    幂等：如果当前消息数尚未跨过新的触发点，直接返回。
    """
    async with async_session_factory() as db:
        try:
            await _check_and_summarize(
                db, conversation_id, api_key, base_url, provider, model
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.warning(
                f"对话 {conversation_id} 摘要任务失败: {e}", exc_info=True
            )


async def _check_and_summarize(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    api_key: str,
    base_url: str,
    provider: str,
    model: str,
) -> None:
    conv = await db.get(Conversation, conversation_id)
    if conv is None:
        return

    msg_count = conv.message_count or 0
    # 至少有 2 个触发间隔的消息（一份保留 + 一份待摘要）才有意义
    if msg_count < SUMMARY_TRIGGER_INTERVAL + RECENT_MESSAGE_WINDOW:
        return

    # 计算这次需要摘要到第几条消息（去掉最近 RECENT_MESSAGE_WINDOW 条）
    target_up_to = msg_count - RECENT_MESSAGE_WINDOW
    # 对齐到 SUMMARY_TRIGGER_INTERVAL 的倍数，避免每次都触发
    target_up_to = (target_up_to // SUMMARY_TRIGGER_INTERVAL) * SUMMARY_TRIGGER_INTERVAL

    prev_summary, prev_up_to = await get_summary(db, conversation_id)
    if target_up_to <= prev_up_to:
        # 已经覆盖到该位置，无需重复摘要
        return

    # 取增量批次：[prev_up_to, target_up_to)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(prev_up_to)
        .limit(target_up_to - prev_up_to)
    )
    batch = result.scalars().all()
    if not batch:
        return

    new_text = _format_messages_for_summary(batch)
    if not new_text:
        return

    try:
        new_summary = await _llm_summarize(
            api_key, base_url, provider, model, prev_summary, new_text
        )
    except Exception as e:
        logger.warning(f"摘要 LLM 调用失败: {e}")
        return

    if not new_summary:
        return

    await _save_summary(db, conversation_id, new_summary, target_up_to)
    logger.info(
        f"对话 {conversation_id} 摘要更新：覆盖到第 {target_up_to} 条 "
        f"(共 {msg_count} 条)，摘要长度 {len(new_summary)}"
    )
