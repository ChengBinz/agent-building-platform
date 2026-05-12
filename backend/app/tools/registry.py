"""Built-in tool registry."""
from app.tools.base import BuiltinTool
from app.tools.web_search import WebSearchTool

BUILTIN_TOOLS: dict[str, BuiltinTool] = {
    "web_search": WebSearchTool(),
}


def get_tool(name: str) -> BuiltinTool | None:
    return BUILTIN_TOOLS.get(name)


def get_tools_schema(names: list[str]) -> list[dict]:
    """Return OpenAI function calling format for the given tool names."""
    schemas = []
    for name in names:
        tool = get_tool(name)
        if tool:
            schemas.append(tool.to_openai_tool())
    return schemas
