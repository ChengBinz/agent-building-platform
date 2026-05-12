"""Multi-format document loader — extracts plain text from supported file types."""
import csv
import io
import os

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def load_document(file_path: str) -> str:
    """Load a document file and return its plain text content.

    Raises ValueError if the file type is not supported.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}")

    if ext in {".txt", ".md"}:
        return _load_text_file(file_path)
    if ext == ".pdf":
        return _load_pdf(file_path)
    if ext == ".docx":
        return _load_docx(file_path)

    raise ValueError(f"不支持的文件类型: {ext}")


# ── Backward-compatible alias ────────────────────────────────────────

def load_text(file_path: str) -> str:
    """Deprecated alias — use load_document() instead."""
    return load_document(file_path)


# ── Format-specific loaders ──────────────────────────────────────────

def _load_text_file(file_path: str) -> str:
    """Read plain text from .txt / .md files."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _load_pdf(file_path: str) -> str:
    """Extract text from a PDF file using pypdf2."""
    from pypdf2 import PdfReader

    reader = PdfReader(file_path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _load_docx(file_path: str) -> str:
    """Extract text from a .docx file."""
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)
