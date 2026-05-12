"""OpenAI-compatible provider (OpenAI, DeepSeek, DashScope, Ollama)."""
from typing import AsyncGenerator

from openai import AsyncOpenAI

from app.engine.base import LLMProvider, StreamChunk

# XML tags used by reasoning models to wrap thinking content
TAG_START = b'\x3cthink\x3e'.decode()   # <think>
TAG_END = b'\x3c/think\x3e'.decode()     # </think>


class OpenAICompatProvider(LLMProvider):
    """Provider for any OpenAI-compatible API.

    Separates reasoning/thinking content from the main response by:
    1. Capturing delta.reasoning_content (standard field for reasoning models)
    2. Parsing <think>...</think> tags from delta.content as a fallback
    """

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
        in_think = False
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # 1) Standard reasoning_content field (DeepSeek, Qwen, etc.)
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                yield {"token": "", "reasoning": delta.reasoning_content}
                continue

            # 2) Parse <think>...</think> tags from content
            if delta.content:
                remaining = delta.content
                while remaining:
                    if in_think:
                        end_idx = remaining.find(TAG_END)
                        if end_idx != -1:
                            if end_idx > 0:
                                yield {"token": "", "reasoning": remaining[:end_idx]}
                            remaining = remaining[end_idx + len(TAG_END):]
                            in_think = False
                        else:
                            yield {"token": "", "reasoning": remaining}
                            break
                    else:
                        start_idx = remaining.find(TAG_START)
                        if start_idx != -1:
                            if start_idx > 0:
                                yield {"token": remaining[:start_idx], "reasoning": None}
                            remaining = remaining[start_idx + len(TAG_START):]
                            in_think = True
                        else:
                            yield {"token": remaining, "reasoning": None}
                            break
