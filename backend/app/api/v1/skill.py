import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillOut,
    SkillToggle,
)
from app.services.skill_service import SkillService

router = APIRouter()


@router.get("/skills/system", response_model=list[SkillOut])
async def list_system_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.list_system_skills()


@router.get("/skills/user", response_model=list[SkillOut])
async def list_user_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.list_user_skills(current_user.id)


@router.post("/skills", response_model=SkillOut, status_code=201)
async def create_skill(
    data: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.create_skill(current_user.id, data)


@router.put("/skills/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: uuid.UUID,
    data: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.update_skill(current_user.id, skill_id, data)


@router.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    await service.delete_skill(current_user.id, skill_id)


@router.put("/skills/{skill_id}/toggle", response_model=SkillOut)
async def toggle_skill(
    skill_id: uuid.UUID,
    data: SkillToggle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SkillService(db)
    return await service.toggle_skill(current_user.id, skill_id, data, is_superuser=current_user.is_superuser)
