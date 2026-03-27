"""Conversation memory management for Gemini chat history."""

from __future__ import annotations

from typing import Any


class MemoryManager:
    """
    This keeps the chat memory context so the bot remembers the conversation.
    It follows SRP because it only stores and gets the history, doing nothing else.
    """

    VALID_ROLES = {"user", "model"}

    def __init__(self) -> None:
        """Initialize an empty in-memory conversation history."""
        self._history: list[dict[str, Any]] = []

    def add_message(self, role: str, text: str) -> None:
        """Append a text message to history in Gemini's content format.

        Args:
            role: Either 'user' or 'model'.
            text: The text payload to store.

        Raises:
            ValueError: If the role is not supported.
        """
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Expected 'user' or 'model'.")

        self._history.append({"role": role, "parts": [{"text": text}]})

    def get_history(self) -> list[dict[str, Any]]:
        """Return a shallow copy of the full conversation history.

        Returns:
            A list copy of the stored Gemini messages.
        """
        return list(self._history)

    def clear(self) -> None:
        """Reset the conversation history."""
        self._history = []

    def get_turn_count(self) -> int:
        """Return the approximate number of conversation turns.

        Returns:
            Half the number of stored history items.
        """
        return len(self._history) // 2
