"""Query-time retrieval from knowledge base collections."""
import uuid

from openai import AsyncOpenAI

from app.config import settings
from app.rag.embedder import embed_query
from app.rag.vector_store import collection_name, get_qdrant_client, search


async def retrieve_relevant_chunks(
    embedding_client: AsyncOpenAI,
    query: str,
    kb_ids: list[uuid.UUID],
    model: str = settings.DEFAULT_EMBEDDING_MODEL,
    top_k: int = settings.RETRIEVAL_TOP_K,
) -> list[dict]:
    """Embed query and search across multiple KB collections.

    Returns a merged, score-sorted list of chunk dicts.
    """
    if not kb_ids:
        return []

    query_vector = await embed_query(embedding_client, query, model=model)

    client = get_qdrant_client()
    all_results: list[dict] = []

    for kb_id in kb_ids:
        col = collection_name(kb_id)
        try:
            results = search(client, col, query_vector, top_k=top_k)
            for r in results:
                r["kb_id"] = str(kb_id)
            all_results.extend(results)
        except Exception:
            continue

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results[:top_k]
