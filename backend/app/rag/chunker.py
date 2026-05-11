"""Recursive character text splitter."""
from app.config import settings


def chunk_text(
    text: str,
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks using recursive character splitting."""
    if not text.strip():
        return []

    separators = ["\n\n", "\n", ". ", " ", ""]
    return _recursive_split(text, separators, chunk_size, chunk_overlap)


def _recursive_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    for sep in separators:
        if sep == "":
            return _split_by_chars(text, chunk_size, chunk_overlap)

        parts = text.split(sep)
        if len(parts) <= 1:
            continue

        return _merge_splits(parts, sep, chunk_size, chunk_overlap)

    return [text] if text.strip() else []


def _merge_splits(
    parts: list[str],
    sep: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    chunks = []
    current = ""

    for part in parts:
        candidate = (current + sep + part).strip() if current else part.strip()

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(part) > chunk_size:
                sub_chunks = _recursive_split(part, ["\n", ". ", " ", ""], chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
                current = ""
            else:
                current = part

    if current.strip():
        chunks.append(current)

    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-chunk_overlap:]
            overlapped.append(prev_tail + " " + chunks[i])
        chunks = overlapped

    return chunks


def _split_by_chars(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks
