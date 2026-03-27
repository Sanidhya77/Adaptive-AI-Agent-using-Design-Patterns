"""Dynamic tool registration and execution support."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any

from tools.base_tool import BaseTool


class ToolRegistry:
    """
    This acts as a Factory and Registry pattern. It stores available tools and runs them.
    It avoids monolithic logic by getting rid of huge if/else tool blocks.
    It follows OCP because adding new tools doesn't require changing this registry code.
    It follows SRP because it only handles tool registration and running.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance under its declared Gemini function name.

        Args:
            tool: The concrete tool instance to register.
        """
        # Tool name comes from declaration, so Agent never needs per-tool wiring.
        name = tool.get_declaration()["name"]
        self._tools[name] = tool

    def auto_register_from_package(self, package_name: str = "tools") -> list[str]:
        """Discover and register tool classes from a package automatically.

        The loader imports all modules inside the package and registers every
        non-abstract subclass of BaseTool that can be instantiated without
        constructor arguments.

        Args:
            package_name: Python package path that contains tool modules.

        Returns:
            Sorted list of registered tool names.
        """
        package = importlib.import_module(package_name)
        if not hasattr(package, "__path__"):
            return []

        for module_info in pkgutil.iter_modules(package.__path__, f"{package_name}."):
            module_name = module_info.name
            if module_name.endswith(".base_tool"):
                continue

            module = importlib.import_module(module_name)
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ != module.__name__:
                    continue
                if cls is BaseTool or not issubclass(cls, BaseTool):
                    continue
                if inspect.isabstract(cls):
                    continue

                try:
                    instance = cls()
                except TypeError:
                    # Skip classes that require constructor args.
                    continue

                self.register(instance)

        return sorted(self._tools.keys())

    def execute(self, tool_name: str, **kwargs: Any) -> str:
        """Execute a registered tool by name and always return a string result.

        Args:
            tool_name: The declared Gemini tool name.
            **kwargs: Tool-specific keyword arguments.

        Returns:
            The tool output or a clean error string.
        """
        if tool_name not in self._tools:
            available = list(self._tools.keys())
            return f"Error: Unknown tool '{tool_name}'. Available: {available}"

        try:
            return self._tools[tool_name].execute(**kwargs)
        except Exception as error:
            return f"Tool '{tool_name}' failed: {str(error)}"

    def get_declarations(self) -> list[dict[str, Any]]:
        """Return Gemini function declarations for all registered tools.

        Returns:
            A list of tool declaration dictionaries.
        """
        return [tool.get_declaration() for tool in self._tools.values()]

    def get_declaration(self, tool_name: str) -> dict[str, Any] | None:
        """Return one tool declaration by name if registered."""
        tool = self._tools.get(tool_name)
        if tool is None:
            return None
        return tool.get_declaration()

    def list_tools(self) -> list[str]:
        """Return the names of all registered tools.

        Returns:
            A list of registered tool names.
        """
        return sorted(self._tools.keys())
