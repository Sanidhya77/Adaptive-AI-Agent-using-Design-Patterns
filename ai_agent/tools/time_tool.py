"""Time lookup tool implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools.base_tool import BaseTool


class TimeTool(BaseTool):
    """Concrete Strategy - returns current date and time."""

    def execute(self, timezone: str = "UTC") -> str:
        """Return the current date and time for the requested timezone.

        Args:
            timezone: An IANA timezone string. Defaults to UTC.

        Returns:
            A formatted timestamp or a helpful error message.
        """
        try:
            zone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            return (
                f"Unknown timezone '{timezone}'. Try 'UTC', 'Europe/London', "
                "'America/New_York', 'Asia/Tokyo'"
            )

        current_time = datetime.now(zone)
        return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")

    def get_declaration(self) -> dict[str, Any]:
        """Return the Gemini function declaration for this tool.

        Returns:
            A JSON-schema-compatible declaration for time lookup.
        """
        return {
            "name": "get_current_time",
            "description": (
                "Returns the current date and time. Optionally for a specific "
                "timezone. Use when user asks what time or date it is."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone name such as UTC or Europe/Riga.",
                    }
                },
            },
        }
