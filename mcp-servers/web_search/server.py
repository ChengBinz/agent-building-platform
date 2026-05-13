"""MCP Server: Web search (Tavily API). Runs standalone on port 9102."""
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

TOOL_DEF = {
    "name": "web_search",
    "description": "搜索互联网获取实时信息。当用户询问实时新闻、最新事件、天气、股价等需要最新数据的问题时使用。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词",
            },
            "max_results": {
                "type": "integer",
                "description": "返回结果数量，默认3",
                "default": 3,
            },
        },
        "required": ["query"],
    },
}


async def _web_search(query: str, max_results: int = 3) -> str:
    if not TAVILY_API_KEY:
        return "错误：未配置 TAVILY_API_KEY，无法执行网页搜索。"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": True,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    answer = data.get("answer", "")
    results = data.get("results", [])

    if not results and not answer:
        return f"未找到与「{query}」相关的搜索结果。"

    parts = []
    if answer:
        parts.append(f"综合回答: {answer}")

    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        snippet = r.get("content", "")
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
        parts.append(f"{i}. {title} — {snippet}")

    return "\n".join(parts)


async def _handle_jsonrpc(request: dict) -> dict:
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "web-search-mcp-server", "version": "1.0.0"},
            },
        }

    if method == "notifications/initialized":
        return {"jsonrpc": "2.0", "method": "notifications/initialized"}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [TOOL_DEF]}}

    if method == "tools/call":
        params = request.get("params", {})
        args = params.get("arguments", {})
        try:
            result_text = await _web_search(args.get("query", ""), args.get("max_results", 3))
        except Exception as e:
            result_text = f"搜索失败: {e}"
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"content": [{"type": "text", "text": result_text}]},
        }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


@app.post("/")
async def jsonrpc_endpoint(request: Request):
    body = await request.json()
    if isinstance(body, list):
        return JSONResponse([await _handle_jsonrpc(r) for r in body])
    return JSONResponse(await _handle_jsonrpc(body))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9102)
