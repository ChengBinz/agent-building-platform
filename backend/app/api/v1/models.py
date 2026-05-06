"""List available LLM providers and models."""
from fastapi import APIRouter

from app.config import settings
from app.schemas.monitoring import ProviderInfo, ModelConfig

router = APIRouter()

# Pre-defined model catalog
_MODEL_CATALOG = [
    ProviderInfo(
        name="OpenAI",
        configured=bool(settings.OPENAI_API_KEY),
        models=[
            ModelConfig(name="gpt-4o-mini", provider="openai", available=True),
            ModelConfig(name="gpt-4o", provider="openai", available=True),
            ModelConfig(name="gpt-4-turbo", provider="openai", available=True),
        ],
    ),
    ProviderInfo(
        name="Anthropic",
        configured=bool(settings.ANTHROPIC_API_KEY),
        models=[
            ModelConfig(name="claude-haiku-4-5", provider="anthropic", available=True),
            ModelConfig(name="claude-sonnet-4-6", provider="anthropic", available=True),
            ModelConfig(name="claude-opus-4-6", provider="anthropic", available=True),
        ],
    ),
    ProviderInfo(
        name="Ollama",
        configured=True,  # Local Ollama is assumed available if configured
        models=[
            ModelConfig(name="qwen3", provider="ollama", available=True),
            ModelConfig(name="llama3", provider="ollama", available=True),
            ModelConfig(name="deepseek-r1", provider="ollama", available=True),
        ],
    ),
    ProviderInfo(
        name="Embedding",
        configured=bool(settings.OPENAI_API_KEY),
        models=[
            ModelConfig(
                name="text-embedding-3-small", provider="openai", available=True
            ),
            ModelConfig(
                name="text-embedding-3-large", provider="openai", available=True
            ),
        ],
    ),
]


@router.get("/models", response_model=list[ProviderInfo])
async def list_models():
    return _MODEL_CATALOG
