import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate, SkillToggle


class SkillService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_system_skills(self) -> list[Skill]:
        result = await self.db.execute(
            select(Skill)
            .where(Skill.is_system == True)
            .order_by(Skill.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_user_skills(self, user_id: uuid.UUID) -> list[Skill]:
        result = await self.db.execute(
            select(Skill)
            .where(Skill.user_id == user_id, Skill.is_system == False)
            .order_by(Skill.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_skill(self, user_id: uuid.UUID, data: SkillCreate) -> Skill:
        skill = Skill(
            user_id=user_id,
            name=data.name,
            description=data.description,
            skill_type=data.skill_type,
            content=data.content,
            is_system=False,
            is_active=True,
            version=data.version,
        )
        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    async def get_skill(self, skill_id: uuid.UUID) -> Skill:
        result = await self.db.execute(
            select(Skill).where(Skill.id == skill_id)
        )
        skill = result.scalar_one_or_none()
        if skill is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能不存在")
        return skill

    async def update_skill(self, user_id: uuid.UUID, skill_id: uuid.UUID, data: SkillUpdate) -> Skill:
        skill = await self.get_skill(skill_id)
        if skill.is_system:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不允许编辑系统内置技能")
        if skill.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权编辑此技能")
        if data.name is not None:
            skill.name = data.name
        if data.description is not None:
            skill.description = data.description
        if data.skill_type is not None:
            skill.skill_type = data.skill_type
        if data.content is not None:
            skill.content = data.content
        if data.version is not None:
            skill.version = data.version
        if data.is_active is not None:
            skill.is_active = data.is_active
        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    async def delete_skill(self, user_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        skill = await self.get_skill(skill_id)
        if skill.is_system:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不允许删除系统内置技能")
        if skill.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此技能")
        await self.db.delete(skill)
        await self.db.flush()

    async def toggle_skill(self, user_id: uuid.UUID, skill_id: uuid.UUID, data: SkillToggle, is_superuser: bool = False) -> Skill:
        skill = await self.get_skill(skill_id)
        if skill.is_system:
            if not is_superuser:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可修改系统技能")
        elif skill.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此技能")
        skill.is_active = data.is_active
        await self.db.flush()
        await self.db.refresh(skill)
        return skill
