"""Async Redis client with safe fallback when REDIS_URL is unset.

Used by MemoryService for caching conversation summaries.
"""
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_client = None  # lazy singleton
_init_failed = False


async def get_redis():
    """Return an async redis.Redis client, or None when Redis is unavailable."""
    global _client, _init_failed

    if _init_failed:
        return None
    if _client is not None:
        return _client
    if not settings.REDIS_URL:
        _init_failed = True
        return None

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        # ping to verify
        await client.ping()
        _client = client
        return _client
    except Exception as e:
        logger.warning(f"Redis 不可用，缓存功能将自动降级: {e}")
        _init_failed = True
        return None


async def redis_get(key: str) -> Optional[str]:
    client = await get_redis()
    if client is None:
        return None
    try:
        return await client.get(key)
    except Exception as e:
        logger.warning(f"Redis GET 失败 ({key}): {e}")
        return None


async def redis_set(key: str, value: str, ex: Optional[int] = None) -> bool:
    """SET with optional TTL (seconds). Returns True on success."""
    client = await get_redis()
    if client is None:
        return False
    try:
        await client.set(key, value, ex=ex)
        return True
    except Exception as e:
        logger.warning(f"Redis SET 失败 ({key}): {e}")
        return False


async def redis_delete(key: str) -> None:
    client = await get_redis()
    if client is None:
        return
    try:
        await client.delete(key)
    except Exception as e:
        logger.warning(f"Redis DEL 失败 ({key}): {e}")
