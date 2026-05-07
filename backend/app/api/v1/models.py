"""List available LLM providers and models."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.monitoring import ProviderInfo, ModelConfig
from app.services.auth_service import AuthService

router = APIRouter()

# Provider definitions with env-var keys for system-level config
_PROVIDER_DEFS = [
    {
        "name": "OpenAI",
        "key": "openai",
        "env_key": settings.OPENAI_API_KEY,
        "models": [
            ModelConfig(name="gpt-4o-mini", provider="openai", available=True),
            ModelConfig(name="gpt-4o", provider="openai", available=True),
            ModelConfig(name="gpt-4-turbo", provider="openai", available=True),
        ],
    },
    {
        "name": "Anthropic",
        "key": "anthropic",
        "env_key": settings.ANTHROPIC_API_KEY,
        "models": [
            ModelConfig(name="claude-haiku-4-5", provider="anthropic", available=True),
            ModelConfig(name="claude-sonnet-4-6", provider="anthropic", available=True),
            ModelConfig(name="claude-opus-4-6", provider="anthropic", available=True),
        ],
    },
    {
        "name": "DeepSeek",
        "key": "deepseek",
        "env_key": settings.DEEPSEEK_API_KEY,
        "models": [
            ModelConfig(name="deepseek-v4-flash", provider="deepseek", available=True),
            ModelConfig(name="deepseek-v4-pro", provider="deepseek", available=True),
        ],
    },
    {
        "name": "阿里百炼",
        "key": "dashscope",
        "env_key": settings.DASHSCOPE_API_KEY,
        "models": [
            ModelConfig(name="qwen-turbo", provider="dashscope", available=True),
            ModelConfig(name="qwen-plus", provider="dashscope", available=True),
            ModelConfig(name="qwen-max", provider="dashscope", available=True),
        ],
    },
    {
        "name": "Ollama",
        "key": "ollama",
        "env_key": True,
        "models": [
            ModelConfig(name="qwen3", provider="ollama", available=True),
            ModelConfig(name="llama3", provider="ollama", available=True),
            ModelConfig(name="deepseek-r1", provider="ollama", available=True),
        ],
    },
    {
        "name": "Embedding",
        "key": "embedding",
        "env_key": settings.OPENAI_API_KEY,
        "models": [
            ModelConfig(name="text-embedding-3-small", provider="openai", available=True),
            ModelConfig(name="text-embedding-3-large", provider="openai", available=True),
        ],
    },
]


@router.get("/models", response_model=list[ProviderInfo])
async def list_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Load user's saved API keys
    service = AuthService(db)
    user_keys = await service.list_api_keys(current_user.id)
    user_key_providers = {k["provider"] for k in user_keys}

    result = []
    for pd in _PROVIDER_DEFS:
        configured = bool(pd["env_key"]) or pd["key"] in user_key_providers
        result.append(
            ProviderInfo(
                name=pd["name"],
                configured=configured,
                models=pd["models"],
            )
        )
    return result
