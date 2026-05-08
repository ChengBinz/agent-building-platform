from typing import AsyncGenerator

# LLM message format
LLMMessage = dict  # {"role": "system"|"user"|"assistant", "content": str}

# Stream chunk from LLM
StreamChunk = dict  # {"token": str}


class LLMProvider:
    """Abstract base for LLM providers."""

    async def generate_stream(
        self, messages: list[LLMMessage], model: str, **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        raise NotImplementedError
