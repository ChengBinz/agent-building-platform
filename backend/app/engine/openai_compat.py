"""OpenAI-compatible provider (OpenAI, DeepSeek, DashScope, Ollama)."""
from typing import AsyncGenerator

from openai import AsyncOpenAI

from app.engine.base import LLMProvider, StreamChunk


class OpenAICompatProvider(LLMProvider):
    """Provider for any OpenAI-compatible API."""

    def __init__(self, api_key: str, base_url: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

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
