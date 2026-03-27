"""Base abstractions for interchangeable agent tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    This acts as the Strategy Pattern interface for all tools.
    It strictly forces every tool to have execute() and get_declaration() methods.
    This prevents monolithic tool logic by keeping every tool in its own class file.
    """

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Run tool logic and always return a string response.

        Args:
            **kwargs: Tool-specific input parameters.

        Returns:
            A human-readable result or error message.
        """

    @abstractmethod
    def get_declaration(self) -> dict[str, Any]:
        """Return the Gemini function-calling JSON schema declaration.

        Returns:
            A declaration dictionary in this format:
            {
                "name": "tool_name",
                "description": "When and why to use this tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param_name": {
                            "type": "string",
                            "description": "what this param is"
                        }
                    },
                    "required": ["param_name"]
                }
            }
        """
