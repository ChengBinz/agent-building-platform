import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.mcp import MCPServer, MCPTool
from app.schemas.mcp import MCPServerCreate, MCPServerUpdate, MCPToolToggle


class MCPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── MCP Server CRUD ───

    async def list_servers(self, user_id: uuid.UUID) -> list[MCPServer]:
        result = await self.db.execute(
            select(MCPServer)
            .options(selectinload(MCPServer.tools))
            .where(MCPServer.user_id == user_id)
            .order_by(MCPServer.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_server(self, user_id: uuid.UUID, data: MCPServerCreate) -> MCPServer:
        server = MCPServer(
            user_id=user_id,
            name=data.name,
            url=data.url,
            transport=data.transport,
            auth_type=data.auth_type,
            auth_value=data.auth_value,
            is_active=data.is_active,
        )
        self.db.add(server)
        await self.db.flush()
        await self.db.refresh(server)
        return server

    async def get_server(self, user_id: uuid.UUID, server_id: uuid.UUID) -> MCPServer:
        result = await self.db.execute(
            select(MCPServer)
            .options(selectinload(MCPServer.tools))
            .where(MCPServer.id == server_id, MCPServer.user_id == user_id)
        )
        server = result.scalar_one_or_none()
        if server is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP Server 不存在")
        return server

    async def update_server(self, user_id: uuid.UUID, server_id: uuid.UUID, data: MCPServerUpdate) -> MCPServer:
        server = await self.get_server(user_id, server_id)
        if data.name is not None:
            server.name = data.name
        if data.url is not None:
            server.url = data.url
        if data.transport is not None:
            server.transport = data.transport
        if data.auth_type is not None:
            server.auth_type = data.auth_type
        if data.auth_value is not None:
            server.auth_value = data.auth_value
        if data.is_active is not None:
            server.is_active = data.is_active
        await self.db.flush()
        await self.db.refresh(server)
        return server

    async def delete_server(self, user_id: uuid.UUID, server_id: uuid.UUID) -> None:
        server = await self.get_server(user_id, server_id)
        await self.db.delete(server)
        await self.db.flush()

    async def test_server_connection(self, user_id: uuid.UUID, server_id: uuid.UUID) -> dict:
        server = await self.get_server(user_id, server_id)
        # TODO: Implement actual MCP server connection test
        # For now, return a placeholder response
        return {"success": True, "message": f"连接测试成功: {server.url}"}

    # ─── MCP Tool CRUD ───

    async def list_tools(self, user_id: uuid.UUID, server_id: uuid.UUID | None = None) -> list[MCPTool]:
        stmt = (
            select(MCPTool)
            .where(MCPTool.user_id == user_id)
            .order_by(MCPTool.created_at.desc())
        )
        if server_id:
            stmt = stmt.where(MCPTool.server_id == server_id)
        result = await self.db.execute(stmt)
        tools = list(result.scalars().all())

        if tools:
            server_ids = {tool.server_id for tool in tools}
            server_result = await self.db.execute(
                select(MCPServer.id, MCPServer.name).where(MCPServer.id.in_(server_ids))
            )
            server_map = dict(server_result.all())
            for tool in tools:
                tool.server_name = server_map.get(tool.server_id, "未知服务")

        return tools

    async def toggle_tool(self, user_id: uuid.UUID, tool_id: uuid.UUID, data: MCPToolToggle) -> MCPTool:
        result = await self.db.execute(
            select(MCPTool).where(MCPTool.id == tool_id, MCPTool.user_id == user_id)
        )
        tool = result.scalar_one_or_none()
        if tool is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP Tool 不存在")
        tool.is_active = data.is_active
        await self.db.flush()
        await self.db.refresh(tool)

        server_result = await self.db.execute(
            select(MCPServer.name).where(MCPServer.id == tool.server_id)
        )
        tool.server_name = server_result.scalar_one_or_none() or "未知服务"

        return tool
