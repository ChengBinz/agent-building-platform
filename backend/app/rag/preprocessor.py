"""Text preprocessing before chunking and embedding."""
import re
import unicodedata


def preprocess_text(text: str) -> str:
    """Clean and normalize raw text before chunking.

    Steps:
    1. Unicode NFKC normalization (full-width → half-width, compatibility chars)
    2. Remove control characters (except newline/tab)
    3. Remove repeated separator lines (---, ===, *** etc.)
    4. Normalize whitespace: collapse multiple spaces/tabs into one
    5. Collapse 3+ consecutive newlines into 2
    6. Strip leading/trailing whitespace per line
    7. Remove lines that are only punctuation or whitespace
    """
    if not text:
        return ""

    # 1. Unicode normalization: full-width → half-width, compatibility chars
    text = unicodedata.normalize("NFKC", text)

    # 2. Remove control characters (keep \n, \t, \r)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # 3. Remove repeated separator lines (lines made entirely of -, =, *, _, ~, #)
    text = re.sub(r"^[=\-~*_#]{3,}\s*$", "", text, flags=re.MULTILINE)

    # 4. Collapse multiple spaces/tabs into one (preserve newlines)
    text = re.sub(r"[^\S\n]+", " ", text)

    # 5. Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 6. Strip leading/trailing whitespace per line
    text = "\n".join(line.strip() for line in text.split("\n"))

    # 7. Remove lines that are only punctuation or whitespace
    text = re.sub(r"^\s*[^\w一-鿿]+\s*$", "", text, flags=re.MULTILINE)

    # Final: collapse excessive newlines again after removals
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def filter_chunks(chunks: list[str], min_length: int = 10) -> list[str]:
    """Remove chunks that are too short or contain no meaningful content.

    Args:
        chunks: list of text chunks
        min_length: minimum character length to keep (default 10)
    """
    filtered = []
    for chunk in chunks:
        stripped = chunk.strip()
        if len(stripped) < min_length:
            continue
        # Skip chunks that are only punctuation/whitespace/symbols
        if not re.search(r"[\w一-鿿]", stripped):
            continue
        filtered.append(stripped)
    return filtered
