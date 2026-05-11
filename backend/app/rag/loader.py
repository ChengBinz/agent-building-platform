"""File loader for text and markdown files."""
import os

SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_text(file_path: str) -> str:
    """Read a txt/md file and return its content.

    Raises ValueError if the file type is not supported.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()
