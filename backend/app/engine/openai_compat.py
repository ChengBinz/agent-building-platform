"""OpenAI-compatible provider (OpenAI, DeepSeek, DashScope, Ollama)."""
from typing import AsyncGenerator

from openai import AsyncOpenAI

from app.engine.base import LLMProvider, StreamChunk


class OpenAICompatProvider(LLMProvider):
    """Provider for any OpenAI-compatible API.

    Separates reasoning/thinking content from the main response by:
    1. Capturing delta.reasoning_content (standard field for reasoning models)
    2. Parsing 思维链...<｜end▁of▁thinking｜> tags from delta.content as a fallback
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

            # 2) Parse 思维链... tags from content (legacy / alternative models)
            if delta.content:
                remaining = delta.content
                while remaining:
                    if in_think:
                        end_idx = remaining.find("</think>")
                        if end_idx != -1:
                            # End of thinking block
                            thinking_part = remaining[:end_idx]
                            remaining = remaining[end_idx + len("</think>"):]
                            in_think = False
                            if thinking_part:
                                yield {"token": "", "reasoning": thinking_part}
                        else:
                            yield {"token": "", "reasoning": remaining}
                            break
                    else:
                        start_idx = remaining.find("</think>")
                        if start_idx != -1:
                            # Content before think tag
                            if start_idx > 0:
                                yield {"token": remaining[:start_idx], "reasoning": None}
                            remaining = remaining[start_idx + len("</think>"):]
                            in_think = True
                        else:
                            yield {"token": remaining, "reasoning": None}
                            break
