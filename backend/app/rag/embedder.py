"""Embedding model wrapper using OpenAI-compatible API."""
from openai import AsyncOpenAI

from app.config import settings

EMBEDDING_BATCH_SIZE = 10


async def get_embedding_client(api_key: str, base_url: str | None = None) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url or "https://api.openai.com/v1",
    )


async def embed_texts(
    client: AsyncOpenAI,
    texts: list[str],
    model: str = settings.DEFAULT_EMBEDDING_MODEL,
) -> list[list[float]]:
    """Embed a list of texts in batches."""
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]
        response = await client.embeddings.create(model=model, input=batch)
        for item in response.data:
            all_embeddings.append(item.embedding)

    return all_embeddings


async def embed_query(
    client: AsyncOpenAI,
    query: str,
    model: str = settings.DEFAULT_EMBEDDING_MODEL,
) -> list[float]:
    """Embed a single query string."""
    response = await client.embeddings.create(model=model, input=[query])
    return response.data[0].embedding
