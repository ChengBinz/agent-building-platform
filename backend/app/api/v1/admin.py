"""User management, system settings (admin only)."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/admin/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.list_users(page=page, page_size=page_size)


@router.get("/admin/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.get_user(user_id)


@router.put("/admin/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.update_user_status(user_id, is_active, is_superuser)


@router.delete("/admin/users/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    await service.delete_user(user_id)


@router.get("/admin/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return await service.get_system_stats()
