"""OpenAI-compatible provider (OpenAI, DeepSeek, DashScope, Ollama)."""
from typing import AsyncGenerator

import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.engine.base import LLMProvider, StreamChunk

# Timeout: 10s connect, 60s read
_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)


class OpenAICompatProvider(LLMProvider):
    """Provider for any OpenAI-compatible API."""

    def __init__(self, api_key: str, base_url: str):
        self.client = AsyncOpenAI(
            api_key=api_key, base_url=base_url, timeout=_TIMEOUT
        )

    async def generate(
        self, messages: list[dict], model: str, **kwargs
    ) -> ChatCompletion:
        """Non-streaming call. Returns the full ChatCompletion object."""
        return await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            **kwargs,
        )

    async def generate_stream(
        self, messages: list[dict], model: str, **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield {"token": delta.content}
