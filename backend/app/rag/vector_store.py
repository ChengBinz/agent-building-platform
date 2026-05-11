"""Qdrant vector store abstraction."""
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from app.config import settings

DEFAULT_DIMENSION = 1536


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def collection_name(kb_id: uuid.UUID) -> str:
    return f"kb_{str(kb_id).replace('-', '_')}"


def ensure_collection(
    client: QdrantClient,
    kb_id: uuid.UUID,
    dimension: int = DEFAULT_DIMENSION,
) -> str:
    """Create the collection for a KB if it doesn't exist."""
    name = collection_name(kb_id)
    collections = [c.name for c in client.get_collections().collections]
    if name not in collections:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )
    return name


def upsert_points(
    client: QdrantClient,
    collection: str,
    points: list[PointStruct],
) -> None:
    client.upsert(collection_name=collection, points=points)


def search(
    client: QdrantClient,
    collection: str,
    query_vector: list[float],
    top_k: int = settings.RETRIEVAL_TOP_K,
) -> list[dict]:
    """Search for similar vectors. Returns list of chunk dicts."""
    results = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=top_k,
    )

    return [
        {
            "text": hit.payload.get("text", ""),
            "document_id": hit.payload.get("document_id", ""),
            "chunk_index": hit.payload.get("chunk_index", 0),
            "filename": hit.payload.get("filename", ""),
            "score": hit.score,
        }
        for hit in results
    ]


def delete_points_by_ids(
    client: QdrantClient,
    collection: str,
    point_ids: list[str],
) -> None:
    if not point_ids:
        return
    client.delete(
        collection_name=collection,
        points_selector=PointIdsList(points=point_ids),
    )


def delete_collection(client: QdrantClient, kb_id: uuid.UUID) -> None:
    name = collection_name(kb_id)
    try:
        client.delete_collection(collection_name=name)
    except Exception:
        pass
