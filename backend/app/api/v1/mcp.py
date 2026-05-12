import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.mcp import (
    MCPServerCreate,
    MCPServerUpdate,
    MCPServerOut,
    MCPToolOut,
    MCPToolToggle,
)
from app.services.mcp_service import MCPService

router = APIRouter()


# ─── MCP Server Endpoints ───

@router.get("/mcp/servers", response_model=list[MCPServerOut])
async def list_mcp_servers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MCPService(db)
    servers = await service.list_servers(current_user.id)
    return [
        MCPServerOut(
            id=s.id,
            user_id=s.user_id,
            name=s.name,
            url=s.url,
            transport=s.transport,
            auth_type=s.auth_type,
            auth_value=s.auth_value,
            is_active=s.is_active,
            tool_count=len(s.tools) if s.tools else 0,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in servers
    ]


@router.post("/mcp/servers", response_model=MCPServerOut, status_code=201)
async def create_mcp_server(
    data: MCPServerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MCPService(db)
    server = await service.create_server(current_user.id, data)
    return MCPServerOut(
        id=server.id,
        user_id=server.user_id,
        name=server.name,
        url=server.url,
        transport=server.transport,
        auth_type=server.auth_type,
        auth_value=server.auth_value,
        is_active=server.is_active,
        tool_count=0,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.put("/mcp/servers/{server_id}", response_model=MCPServerOut)
async def update_mcp_server(
    server_id: uuid.UUID,
    data: MCPServerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MCPService(db)
    server = await service.update_server(current_user.id, server_id, data)
    return MCPServerOut(
        id=server.id,
        user_id=server.user_id,
        name=server.name,
        url=server.url,
        transport=server.transport,
        auth_type=server.auth_type,
        auth_value=server.auth_value,
        is_active=server.is_active,
        tool_count=len(server.tools) if server.tools else 0,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.delete("/mcp/servers/{server_id}", status_code=204)
async def delete_mcp_server(
    server_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MCPService(db)
    await service.delete_server(current_user.id, server_id)


@router.post("/mcp/servers/{server_id}/test")
async def test_mcp_server_connection(
    server_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MCPService(db)
    return await service.test_server_connection(current_user.id, server_id)


@router.post("/mcp/servers/{server_id}/sync", response_model=list[MCPToolOut])
async def sync_mcp_tools(
    server_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MCPService(db)
    return await service.sync_tools(current_user.id, server_id)


# ─── MCP Tool Endpoints ───

@router.get("/mcp/tools", response_model=list[MCPToolOut])
async def list_mcp_tools(
    server_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MCPService(db)
    return await service.list_tools(current_user.id, server_id=server_id)


@router.put("/mcp/tools/{tool_id}/toggle", response_model=MCPToolOut)
async def toggle_mcp_tool(
    tool_id: uuid.UUID,
    data: MCPToolToggle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MCPService(db)
    return await service.toggle_tool(current_user.id, tool_id, data)
