"""Multi-format document loader — extracts plain text from supported file types."""
import csv
import os

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv"}


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
    if ext == ".csv":
        return _load_csv(file_path)

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
    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def _load_docx(file_path: str) -> str:
    """Extract text from a .docx file.

    Tries python-docx first; falls back to manual ZIP/XML extraction for
    malformed files (e.g. WPS-generated with missing Content_Types entries).
    """
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        if paragraphs:
            return "\n".join(paragraphs)
        # If python-docx succeeds but returns no text, try fallback too
    except Exception:
        pass

    # Fallback: manually parse word/document.xml from the ZIP archive
    import xml.etree.ElementTree as ET
    import zipfile

    with zipfile.ZipFile(file_path, "r") as z:
        if "word/document.xml" not in z.namelist():
            raise ValueError("无效的 docx 文件：缺少 word/document.xml")
        xml_content = z.read("word/document.xml")

    root = ET.fromstring(xml_content)
    # docx XML namespace
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    # Collect all text-bearing blocks: paragraphs (<w:p>) and table rows (<w:tr>)
    text_blocks: list[str] = []
    # Use iter() to traverse the whole tree — catches paragraphs inside tables too
    for elem in root.iter():
        tag = elem.tag
        if tag == f"{{{ns['w']}}}p":
            line = _extract_docx_text(elem, ns)
            if line:
                text_blocks.append(line)
        elif tag == f"{{{ns['w']}}}tr":
            # Table row: join cell texts with tabs for readability
            cells = []
            for tc in elem.iterfind(".//w:tc", ns):
                cell_text = _extract_docx_text(tc, ns)
                cells.append(cell_text)
            row_text = "\t".join(c for c in cells if c)
            if row_text:
                text_blocks.append(row_text)
    return "\n".join(text_blocks)


def _extract_docx_text(elem, ns: dict[str, str]) -> str:
    """Extract all <w:t> text inside an XML element, joined."""
    texts = []
    for t in elem.iterfind(".//w:t", ns):
        if t.text:
            texts.append(t.text)
    return "".join(texts).strip()


def _load_csv(file_path: str) -> str:
    """Extract text from a CSV file, joining cells with separators."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = [" | ".join(row) for row in reader if any(cell.strip() for cell in row)]
        return "\n".join(rows)
