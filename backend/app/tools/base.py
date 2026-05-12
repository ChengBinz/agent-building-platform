"""Base class for built-in tools."""
from abc import ABC, abstractmethod


class BuiltinTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool and return the result as a string."""

    def to_openai_tool(self) -> dict:
        """Return the tool definition in OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
