"""MCP Server: Weather lookup (wttr.in). Runs standalone on port 9100."""
import uuid

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio

app = FastAPI()

TOOL_DEF = {
    "name": "weather",
    "description": "查询指定城市的实时天气信息，包括温度、天气状况、湿度、风速等。",
    "inputSchema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称，如 Beijing、上海、Tokyo"},
        },
        "required": ["city"],
    },
}


def _query_weather(city: str) -> str:
    resp = httpx.get(f"https://wttr.in/{city}?format=j1&lang=zh", timeout=10)
    resp.raise_for_status()
    data = resp.json()

    current = data.get("current_condition", [{}])[0]
    area = data.get("nearest_area", [{}])[0]
    area_name = area.get("areaName", [{}])[0].get("value", city)
    country = area.get("country", [{}])[0].get("value", "")
    temp_c = current.get("temp_C", "N/A")
    feels_like = current.get("FeelsLikeC", "N/A")
    humidity = current.get("humidity", "N/A")
    wind_speed = current.get("windspeedKmph", "N/A")
    wind_dir = current.get("winddir16Point", "")
    desc_list = current.get("lang_zh", current.get("weatherDesc", [{}]))
    desc = desc_list[0].get("value", "未知") if desc_list else "未知"
    visibility = current.get("visibility", "N/A")
    uv = current.get("uvIndex", "N/A")

    return (
        f"📍 {area_name}, {country}\n"
        f"🌡️ 温度: {temp_c}°C (体感 {feels_like}°C)\n"
        f"☁️ 天气: {desc}\n"
        f"💧 湿度: {humidity}%\n"
        f"🌬️ 风速: {wind_speed} km/h {wind_dir}\n"
        f"👁️ 能见度: {visibility} km\n"
        f"☀️ 紫外线指数: {uv}"
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
                "serverInfo": {"name": "weather-mcp-server", "version": "1.0.0"},
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
            result_text = _query_weather(args.get("city", ""))
        except Exception as e:
            result_text = f"天气查询失败: {e}"
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {"content": [{"type": "text", "text": result_text}]},
        }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}


# ── SSE transport ──

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


# ── Simple HTTP transport ──

@app.post("/")
async def jsonrpc_endpoint(request: Request):
    body = await request.json()
    if isinstance(body, list):
        return JSONResponse([_handle_jsonrpc(r) for r in body])
    return JSONResponse(_handle_jsonrpc(body))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9100)
