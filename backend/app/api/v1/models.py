"""LLM factories and user-added model management (RAGFlow-style)."""
import uuid

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.llm import (
    FactoryInfo,
    LLMModelCreate,
    LLMModelOut,
    LLMModelUpdate,
)
from app.services.llm_service import LLMService

router = APIRouter()


# ── Static factory catalog ──

@router.get("/llm/factories", response_model=list[FactoryInfo])
async def list_factories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LLMService(db)
    return await service.list_factories()


# ── User-added models ──

@router.get("/llm/models", response_model=list[LLMModelOut])
async def list_user_models(
    model_type: str | None = Query(default=None, description="chat/embedding/rerank/…"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LLMService(db)
    return await service.list_models(current_user.id, model_type=model_type)


@router.post("/llm/models", response_model=LLMModelOut, status_code=201)
async def add_user_model(
    data: LLMModelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LLMService(db)
    await service.add_model(current_user.id, data)
    # return enriched view (with masked key + is_default flag)
    models = await service.list_models(current_user.id, model_type=data.model_type)
    for m in models:
        if m.factory == data.factory and m.model_name == data.model_name:
            return m
    # defensive fallback: shouldn't reach here
    return models[0]


@router.put("/llm/models/{model_id}", response_model=LLMModelOut)
async def update_user_model(
    model_id: uuid.UUID,
    data: LLMModelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LLMService(db)
    m = await service.update_model(current_user.id, model_id, data)
    models = await service.list_models(current_user.id, model_type=m.model_type)
    for item in models:
        if item.id == m.id:
            return item
    return models[0]


@router.delete("/llm/models/{model_id}", status_code=204)
async def delete_user_model(
    model_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LLMService(db)
    await service.delete_model(current_user.id, model_id)


# ── Default models ──

@router.get("/llm/defaults")
async def get_defaults(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LLMService(db)
    return await service.get_defaults(current_user.id)


@router.post("/llm/defaults", status_code=204)
async def set_default(
    model_type: str = Body(..., embed=True),
    llm_model_id: uuid.UUID = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = LLMService(db)
    await service.set_default(current_user.id, model_type, llm_model_id)


# ── Fetch available models from provider ──

class FetchModelsRequest(BaseModel):
    api_key: str
    base_url: str


class FetchModelsResponse(BaseModel):
    models: list[str]


@router.post("/llm/fetch-models", response_model=FetchModelsResponse)
async def fetch_available_models(
    data: FetchModelsRequest,
    current_user: User = Depends(get_current_user),
):
    """Call the provider's /models endpoint to list available model IDs."""
    from openai import AsyncOpenAI

    try:
        client = AsyncOpenAI(api_key=data.api_key, base_url=data.base_url, timeout=15.0)
        response = await client.models.list()
        model_ids = sorted([m.id for m in response.data])
        return FetchModelsResponse(models=model_ids)
    except Exception as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取模型列表失败: {str(e)[:200]}",
        )


# ── Test model connectivity ──

class TestModelRequest(BaseModel):
    api_key: str
    base_url: str
    model_name: str
    model_type: str = "chat"  # chat / embedding / rerank / ...


class TestModelResponse(BaseModel):
    success: bool
    message: str
    reply: str | None = None


@router.post("/llm/test-model", response_model=TestModelResponse)
async def test_model_connection(
    data: TestModelRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a minimal request to verify the model works.
    Uses chat completion for chat models, embeddings API for embedding models."""
    from openai import AsyncOpenAI

    try:
        client = AsyncOpenAI(api_key=data.api_key, base_url=data.base_url, timeout=30.0)

        if data.model_type == "embedding":
            response = await client.embeddings.create(
                model=data.model_name,
                input="hello",
            )
            dim = len(response.data[0].embedding) if response.data else 0
            return TestModelResponse(
                success=True,
                message=f"连接成功，向量维度: {dim}",
                reply=f"dim={dim}",
            )
        else:
            # chat / image2text / rerank / others — use chat completion
            response = await client.chat.completions.create(
                model=data.model_name,
                messages=[{"role": "user", "content": "Hi, reply with 'ok' only."}],
                max_tokens=10,
            )
            reply = response.choices[0].message.content if response.choices else ""
            return TestModelResponse(success=True, message="连接成功", reply=reply)

    except Exception as e:
        return TestModelResponse(success=False, message=f"连接失败: {str(e)[:300]}", reply=None)
