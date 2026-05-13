"""Unified tool service — resolves tools from MCP servers.

Provides a clean interface for chat_service:
  - get_tool_schemas(tool_names) → OpenAI function-calling format
  - execute_tool(tool_name, args, user_id, db) → result string
"""
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp import MCPServer, MCPTool
from app.services.mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)


async def get_tool_schemas(
    tool_names: list[str], user_id: uuid.UUID, db: AsyncSession
) -> list[dict]:
    """Return OpenAI function-calling schemas for the given tool names."""
    schemas: list[dict] = []

    if not tool_names:
        return schemas

    result = await db.execute(
        select(MCPTool).where(
            MCPTool.user_id == user_id,
            MCPTool.name.in_(tool_names),
            MCPTool.is_active == True,
        )
    )
    mcp_tools = result.scalars().all()
    for t in mcp_tools:
        schemas.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.input_schema or {"type": "object", "properties": {}},
            },
        })

    return schemas


async def execute_tool(
    tool_name: str,
    arguments: dict,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> str:
    """Execute a tool by name via MCP."""
    result = await db.execute(
        select(MCPTool)
        .join(MCPServer, MCPTool.server_id == MCPServer.id)
        .where(
            MCPTool.user_id == user_id,
            MCPTool.name == tool_name,
            MCPTool.is_active == True,
            MCPServer.is_active == True,
        )
    )
    mcp_tool = result.scalar_one_or_none()
    if not mcp_tool:
        return f"错误：未找到工具 {tool_name}"

    server_result = await db.execute(
        select(MCPServer.url).where(MCPServer.id == mcp_tool.server_id)
    )
    server_url = server_result.scalar_one_or_none()
    if not server_url:
        return f"错误：工具 {tool_name} 关联的 MCP 服务器不存在"

    return await call_mcp_tool(server_url, tool_name, arguments)


async def get_all_tools_info(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    """Return all available MCP tools for the user."""
    tools: list[dict] = []

    result = await db.execute(
        select(MCPTool).where(
            MCPTool.user_id == user_id,
            MCPTool.is_active == True,
        )
    )
    for t in result.scalars().all():
        tools.append({
            "name": t.name,
            "description": t.description or "",
            "source": "mcp",
        })

    return tools
