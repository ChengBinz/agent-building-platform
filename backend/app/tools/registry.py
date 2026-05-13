"""Built-in tool registry."""
from app.tools.base import BuiltinTool

BUILTIN_TOOLS: dict[str, BuiltinTool] = {}


def get_tool(name: str) -> BuiltinTool | None:
    return BUILTIN_TOOLS.get(name)


def get_all_builtin_tools_info() -> list[dict]:
    """Return built-in tool info (name + description)."""
    return [
        {"name": tool.name, "description": tool.description, "source": "builtin"}
        for tool in BUILTIN_TOOLS.values()
    ]


def get_tools_schema(names: list[str]) -> list[dict]:
    """Return OpenAI function calling format for the given tool names."""
    schemas = []
    for name in names:
        tool = get_tool(name)
        if tool:
            schemas.append(tool.to_openai_tool())
    return schemas
