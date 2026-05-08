"""Provider registry — returns provider instance by key."""
from app.engine.base import LLMProvider
from app.engine.openai_compat import OpenAICompatProvider

# Default base URLs per provider
_DEFAULT_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "anthropic": "https://api.anthropic.com",
    "ollama": "http://localhost:11434/v1",
    "embedding": "https://api.openai.com/v1",
}


def get_provider(provider: str, api_key: str, base_url: str | None = None) -> LLMProvider:
    """Create and return an LLM provider instance."""
    base = base_url or _DEFAULT_BASE_URLS.get(provider, "https://api.openai.com/v1")
    # All currently supported providers use OpenAI-compatible API
    return OpenAICompatProvider(api_key=api_key, base_url=base)
