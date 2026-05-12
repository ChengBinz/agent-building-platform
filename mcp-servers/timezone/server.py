"""MCP Server: Timezone lookup (Python stdlib). Runs standalone on port 9101."""
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio

app = FastAPI()

TOOL_DEF = {
    "name": "timezone",
    "description": "查询指定时区或城市的当前日期和时间。支持时区名称（如 Asia/Shanghai）或常见城市名（如 北京、纽约）。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "时区名称（如 Asia/Shanghai）或城市名（如 北京、纽约、东京）",
            },
        },
        "required": ["timezone"],
    },
}

COMMON_TIMEZONES = {
    "中国": "Asia/Shanghai", "上海": "Asia/Shanghai", "北京": "Asia/Shanghai",
    "东京": "Asia/Tokyo", "日本": "Asia/Tokyo",
    "纽约": "America/New_York", "美国东部": "America/New_York",
    "洛杉矶": "America/Los_Angeles", "美国西部": "America/Los_Angeles",
    "伦敦": "Europe/London", "英国": "Europe/London",
    "巴黎": "Europe/Paris", "欧洲": "Europe/Paris",
    "悉尼": "Australia/Sydney", "澳大利亚": "Australia/Sydney",
    "印度": "Asia/Kolkata", "迪拜": "Asia/Dubai",
    "首尔": "Asia/Seoul", "韩国": "Asia/Seoul",
    "新加坡": "Asia/Singapore", "莫斯科": "Europe/Moscow", "俄罗斯": "Europe/Moscow",
    "UTC": "UTC", "格林威治": "UTC",
}


def _query_timezone(tz_input: str) -> str:
    tz_name = COMMON_TIMEZONES.get(tz_input, tz_input)
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        available = ", ".join(sorted(COMMON_TIMEZONES.keys()))
        return f"错误：无法识别时区「{tz_input}」。支持的城市：{available}"

    now = datetime.now(tz)
    weekday_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
    weekday = weekday_map[now.weekday()]

    return (
        f"📍 {tz_name}\n"
        f"📅 日期: {now.strftime('%Y年%m月%d日')} {weekday}\n"
        f"🕐 时间: {now.strftime('%H:%M:%S')}\n"
        f"🌐 UTC偏移: {now.strftime('%z')}"
    )


def _handle_jsonrpc(request: dict) -> dict:
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "timezone-mcp-server", "version": "1.0.0"},
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
            result_text = _query_timezone(args.get("timezone", ""))
        except Exception as e:
            result_text = f"时区查询失败: {e}"
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"content": [{"type": "text", "text": result_text}]},
        }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


@app.get("/sse")
async def sse_endpoint():
    session_id = str(uuid.uuid4())

    async def event_stream():
        yield f"event: endpoint\ndata: /messages?session_id={session_id}\n\n"
        while True:
            await asyncio.sleep(30)
            yield "event: ping\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/messages")
async def messages_endpoint(request: Request):
    body = await request.json()
    return JSONResponse(_handle_jsonrpc(body))


@app.post("/")
async def jsonrpc_endpoint(request: Request):
    body = await request.json()
    if isinstance(body, list):
        return JSONResponse([_handle_jsonrpc(r) for r in body])
    return JSONResponse(_handle_jsonrpc(body))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9101)
