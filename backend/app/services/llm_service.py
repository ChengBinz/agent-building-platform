"""LLM factory catalog + user-added model CRUD + default model management."""
import json
import uuid
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_model import DefaultModel, LLMModel
from app.schemas.llm import (
    FactoryInfo,
    LLMModelCreate,
    LLMModelOut,
    LLMModelUpdate,
)

_FACTORIES_FILE = Path(__file__).resolve().parent.parent / "data" / "llm_factories.json"


@lru_cache(maxsize=1)
def load_factories() -> list[FactoryInfo]:
    """Load and cache the static llm_factories.json."""
    with _FACTORIES_FILE.open("r", encoding="utf-8") as fp:
        raw = json.load(fp)
    factories = [FactoryInfo(**f) for f in raw.get("factory_llm_infos", [])]
    # sort by rank desc (so most popular appear first)
    factories.sort(key=lambda f: int(f.rank or "0"), reverse=True)
    return factories


def _mask_key(key: str | None) -> str | None:
    if not key:
        return None
    if len(key) <= 4:
        return "****"
    return "****" + key[-4:]


class LLMService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Factory catalog ──

    async def list_factories(self) -> list[FactoryInfo]:
        return load_factories()

    def _find_factory(self, factory_name: str) -> FactoryInfo | None:
        for f in load_factories():
            if f.name == factory_name:
                return f
        return None

    # ── User models CRUD ──

    async def list_models(
        self, user_id: uuid.UUID, model_type: str | None = None
    ) -> list[LLMModelOut]:
        stmt = select(LLMModel).where(LLMModel.user_id == user_id)
        if model_type:
            stmt = stmt.where(LLMModel.model_type == model_type)
        stmt = stmt.order_by(LLMModel.created_at.desc())
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        # fetch current defaults map {model_type: llm_model_id}
        dresult = await self.db.execute(
            select(DefaultModel).where(DefaultModel.user_id == user_id)
        )
        default_map = {d.model_type: d.llm_model_id for d in dresult.scalars().all()}

        return [
            LLMModelOut(
                id=m.id,
                factory=m.factory,
                model_type=m.model_type,
                model_name=m.model_name,
                api_key_masked=_mask_key(m.api_key),
                base_url=m.base_url,
                max_tokens=m.max_tokens,
                is_tools=m.is_tools,
                tags=m.tags,
                is_active=m.is_active,
                is_default=default_map.get(m.model_type) == m.id,
            )
            for m in rows
        ]

    async def get_model(self, user_id: uuid.UUID, model_id: uuid.UUID) -> LLMModel:
        result = await self.db.execute(
            select(LLMModel).where(LLMModel.id == model_id, LLMModel.user_id == user_id)
        )
        m = result.scalar_one_or_none()
        if m is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模型不存在")
        return m

    async def add_model(self, user_id: uuid.UUID, data: LLMModelCreate) -> LLMModel:
        factory = self._find_factory(data.factory)
        if factory is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未知的模型工厂：{data.factory}",
            )

        # check duplicate
        exists = await self.db.execute(
            select(LLMModel).where(
                LLMModel.user_id == user_id,
                LLMModel.factory == data.factory,
                LLMModel.model_name == data.model_name,
                LLMModel.model_type == data.model_type,
            )
        )
        if exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该模型已添加，请勿重复配置",
            )

        # fill defaults from factory catalog if the model is known there
        resolved_tags = data.tags
        resolved_is_tools = data.is_tools
        resolved_max_tokens = data.max_tokens
        for mi in factory.llm:
            if mi.llm_name == data.model_name and mi.model_type == data.model_type:
                if resolved_tags is None:
                    resolved_tags = mi.tags
                if data.max_tokens is None and mi.max_tokens is not None:
                    resolved_max_tokens = mi.max_tokens
                if not data.is_tools:
                    resolved_is_tools = mi.is_tools
                break

        m = LLMModel(
            user_id=user_id,
            factory=data.factory,
            model_type=data.model_type,
            model_name=data.model_name,
            api_key=data.api_key,
            base_url=data.base_url or factory.url,
            max_tokens=resolved_max_tokens,
            is_tools=resolved_is_tools,
            tags=resolved_tags,
            extra=data.extra,
            is_active=True,
        )
        self.db.add(m)
        await self.db.flush()
        await self.db.refresh(m)

        # auto-set as default if there isn't one yet for this type
        existing_default = await self.db.execute(
            select(DefaultModel).where(
                DefaultModel.user_id == user_id,
                DefaultModel.model_type == data.model_type,
            )
        )
        if existing_default.scalar_one_or_none() is None:
            self.db.add(
                DefaultModel(
                    user_id=user_id,
                    model_type=data.model_type,
                    llm_model_id=m.id,
                )
            )
            await self.db.flush()

        return m

    async def update_model(
        self, user_id: uuid.UUID, model_id: uuid.UUID, data: LLMModelUpdate
    ) -> LLMModel:
        m = await self.get_model(user_id, model_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(m, field, value)
        await self.db.flush()
        await self.db.refresh(m)
        return m

    async def delete_model(self, user_id: uuid.UUID, model_id: uuid.UUID) -> None:
        m = await self.get_model(user_id, model_id)
        # clean up related default first (cascade will also do this)
        await self.db.execute(
            select(DefaultModel).where(DefaultModel.llm_model_id == m.id)
        )
        await self.db.delete(m)
        await self.db.flush()

    # ── Defaults ──

    async def set_default(
        self, user_id: uuid.UUID, model_type: str, model_id: uuid.UUID
    ) -> None:
        m = await self.get_model(user_id, model_id)
        if m.model_type != model_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"模型类型不匹配，期望 {model_type}，实际 {m.model_type}",
            )

        result = await self.db.execute(
            select(DefaultModel).where(
                DefaultModel.user_id == user_id,
                DefaultModel.model_type == model_type,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.llm_model_id = model_id
        else:
            self.db.add(
                DefaultModel(
                    user_id=user_id,
                    model_type=model_type,
                    llm_model_id=model_id,
                )
            )
        await self.db.flush()

    async def get_defaults(self, user_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(DefaultModel, LLMModel)
            .join(LLMModel, DefaultModel.llm_model_id == LLMModel.id)
            .where(DefaultModel.user_id == user_id)
        )
        return [
            {
                "model_type": d.model_type,
                "llm_model_id": d.llm_model_id,
                "factory": m.factory,
                "model_name": m.model_name,
            }
            for d, m in result.all()
        ]

    # ── Runtime lookup (used by chat_service / rag) ──

    async def get_user_model(
        self,
        user_id: uuid.UUID,
        model_type: str,
        *,
        factory: str | None = None,
        model_name: str | None = None,
    ) -> LLMModel | None:
        """Return a model matching the criteria, or the user's default for the type."""
        stmt = select(LLMModel).where(
            LLMModel.user_id == user_id,
            LLMModel.model_type == model_type,
            LLMModel.is_active == True,
        )
        if factory:
            stmt = stmt.where(LLMModel.factory == factory)
        if model_name:
            stmt = stmt.where(LLMModel.model_name == model_name)

        result = await self.db.execute(stmt.limit(1))
        m = result.scalar_one_or_none()
        if m is not None:
            return m

        # fall back to default
        dres = await self.db.execute(
            select(DefaultModel).where(
                DefaultModel.user_id == user_id,
                DefaultModel.model_type == model_type,
            )
        )
        d = dres.scalar_one_or_none()
        if d is None:
            return None
        return await self.db.get(LLMModel, d.llm_model_id)
