"""Text preprocessing before chunking and embedding. RAG知识库专用文本清洗"""
import re
import unicodedata


def preprocess_text(text: str) -> str:
    """
    知识库文本预处理（适配中文/英文/Markdown）
    1. Unicode标准化 2. 去除控制字符 3. 清理分隔线 4. 空白符规范化
    5. 清理空行 6. 清理无效行 7. 最终格式化
    """
    if not text or not text.strip():
        return ""

    # 1. Unicode NFKC 标准化（全角转半角，兼容字符统一）
    text = unicodedata.normalize("NFKC", text)

    # 2. 删除控制字符（保留换行、制表符）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # 3. 删除 Markdown 无用分隔线（--- / === / *** 等整行装饰符）
    text = re.sub(r"^\s*[=\-~*_#]{3,}\s*$", "", text, flags=re.MULTILINE)

    # 4. 合并空格/制表符（不合并换行）
    text = re.sub(r"[^\S\n]+", " ", text)

    # 5. 合并多余空行：3+ 空行 → 2 个空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 6. 每行去除首尾空格
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # 7. 删除【纯标点/纯符号/空白】的无效行（支持中英文）
    text = re.sub(r"^\s*[^\w\s一-龥]*\s*$", "", text, flags=re.MULTILINE)

    # 最终清理：再次合并空行 + 首尾去空格
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return text


def filter_chunks(chunks: list[str], min_length: int = 15) -> list[str]:
    """
    过滤无效文本块（RAG分块专用）
    Args:
        chunks: 文本分块列表
        min_length: 最小有效长度（默认15，更适配中文）
    Returns: 过滤后的高质量分块
    """
    filtered = []
    # 匹配：中文/英文/数字（有实际语义的字符）
    content_pattern = re.compile(r"[\w一-龥]")

    for chunk in chunks:
        stripped = chunk.strip()
        # 过滤条件1：长度过短
        if len(stripped) < min_length:
            continue
        # 过滤条件2：无实际语义内容
        if not content_pattern.search(stripped):
            continue
        filtered.append(stripped)

    return filtered