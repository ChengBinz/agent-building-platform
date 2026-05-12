from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import tool_service

router = APIRouter()


@router.get("/tools")
async def list_tools(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available tools (built-in + MCP) for the current user."""
    return await tool_service.get_all_tools_info(current_user.id, db)
