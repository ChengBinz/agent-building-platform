"""Web search tool using Tavily API."""
import asyncio
import logging

from tavily import TavilyClient

from app.config import settings
from app.tools.base import BuiltinTool

logger = logging.getLogger(__name__)


class WebSearchTool(BuiltinTool):
    name = "web_search"
    description = "搜索互联网获取实时信息。当用户询问实时新闻、最新事件、天气、股价等需要最新数据的问题时使用。"
    parameters = {
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
    }

    async def execute(self, **kwargs) -> str:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 3)

        api_key = settings.TAVILY_API_KEY
        if not api_key:
            return "错误：未配置 TAVILY_API_KEY，无法执行网页搜索。"

        try:
            client = TavilyClient(api_key=api_key)
            response = await asyncio.to_thread(
                client.search,
                query=query,
                max_results=max_results,
                search_depth="basic",
                include_answer=True,
            )

            # Tavily 自带的摘要回答（如果有）
            answer = response.get("answer", "")
            results = response.get("results", [])

            if not results and not answer:
                return f"未找到与「{query}」相关的搜索结果。"

            parts = []
            if answer:
                parts.append(f"综合回答: {answer}")

            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                snippet = r.get("content", "")
                # 截断过长的摘要
                if len(snippet) > 200:
                    snippet = snippet[:200] + "..."
                parts.append(f"{i}. {title} — {snippet}")

            return "\n".join(parts)
        except Exception as e:
            logger.exception("Web search failed")
            return f"搜索失败: {e}"
