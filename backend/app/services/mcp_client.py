"""Lightweight MCP client — connects to MCP servers via HTTP JSON-RPC."""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)


async def call_mcp_tool(server_url: str, tool_name: str, arguments: dict[str, Any]) -> str:
    """Call a tool on an MCP server and return the text result."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(server_url.rstrip("/") + "/", json=payload)
            resp.raise_for_status()
            result = resp.json()

        if "error" in result:
            return f"MCP 错误: {result['error'].get('message', '未知错误')}"

        content = result.get("result", {}).get("content", [])
        texts = [item["text"] for item in content if item.get("type") == "text"]
        return "\n".join(texts) if texts else "(工具返回了空结果)"
    except Exception as e:
        logger.exception(f"MCP tool call failed: {server_url} / {tool_name}")
        return f"MCP 调用失败: {e}"


async def discover_tools(server_url: str) -> list[dict]:
    """Connect to an MCP server and discover its tools."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ai-agent-platform", "version": "1.0.0"},
        },
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(server_url.rstrip("/") + "/", json=payload)
            resp.raise_for_status()

            # Get tools list
            list_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
            resp2 = await client.post(server_url.rstrip("/") + "/", json=list_payload)
            resp2.raise_for_status()
            result = resp2.json()

        tools = result.get("result", {}).get("tools", [])
        return tools
    except Exception as e:
        logger.exception(f"MCP tool discovery failed: {server_url}")
        return []
