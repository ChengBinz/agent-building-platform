"""Usage stats, token logs."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.monitoring import UsageSummary, TokenUsageByModel
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get("/monitoring/usage", response_model=UsageSummary)
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MonitoringService(db)
    return await service.get_usage_summary()


@router.get("/monitoring/usage-by-model", response_model=list[TokenUsageByModel])
async def get_usage_by_model(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MonitoringService(db)
    return await service.get_usage_by_model()
