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

        # Accumulate streaming tool calls
        accumulated_tool_calls: dict[int, dict] = {}

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            if delta.content:
                yield {"token": delta.content}

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in accumulated_tool_calls:
                        accumulated_tool_calls[idx] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    entry = accumulated_tool_calls[idx]
                    if tc.id:
                        entry["id"] = tc.id
                    if tc.type:
                        entry["type"] = tc.type
                    if tc.function:
                        if tc.function.name:
                            entry["function"]["name"] = tc.function.name
                        if tc.function.arguments:
                            entry["function"]["arguments"] += tc.function.arguments

        # Yield assembled tool calls at the end of the stream
        if accumulated_tool_calls:
            yield {"tool_calls": [accumulated_tool_calls[i] for i in sorted(accumulated_tool_calls)]}
