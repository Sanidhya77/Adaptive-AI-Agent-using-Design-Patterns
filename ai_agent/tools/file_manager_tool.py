"""Unified secure local file manager tool (read + write)."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from tools.base_tool import BaseTool


class FileManagerTool(BaseTool):
    """
    This is Custom Tool 2. It reads from text files and writes down text into files.
    It returns a valid JSON schema declaration for Gemini.
    It includes error handling for bad paths and permissions.
    """

    ALLOWED_READ_EXTENSIONS: set[str] = {".txt", ".md", ".csv", ".json", ".log"}
    MAX_READ_SIZE_BYTES: int = 50_000
    OUTPUT_DIR: str = "saved_outputs"

    def execute(self, action: str, file_path: str, content: str = "") -> str:
        """Perform a read or write operation.

        Args:
            action: Either "read" or "write".
            file_path: Target filename.
            content: Text to write when action is "write".

        Returns:
            Operation result or a clear error message.
        """
        normalized_action = (action or "").strip().lower()
        if normalized_action not in {"read", "write"}:
            return "Error: action must be either 'read' or 'write'."

        safe_name = os.path.basename(file_path)
        if safe_name == "":
            return "Error: Invalid file path provided."

        if normalized_action == "read":
            return self._read_file(safe_name)

        return self._write_file(safe_name, content)

    def _read_file(self, safe_name: str) -> str:
        extension = os.path.splitext(safe_name)[1].lower()
        if extension not in self.ALLOWED_READ_EXTENSIONS:
            return (
                f"Error: Extension '{extension or '[no extension]'}' is not allowed for read. "
                f"Allowed extensions: {sorted(self.ALLOWED_READ_EXTENSIONS)}"
            )

        candidate_paths = [safe_name, os.path.join(self.OUTPUT_DIR, safe_name)]
        target_path = next((path for path in candidate_paths if os.path.exists(path)), None)
        if not target_path:
            return f"Error: File '{safe_name}' not found in project root or '{self.OUTPUT_DIR}'."

        if os.path.getsize(target_path) > self.MAX_READ_SIZE_BYTES:
            return (
                f"Error: File '{safe_name}' is too large. "
                f"Max size is {self.MAX_READ_SIZE_BYTES} bytes."
            )

        try:
            with open(target_path, "r", encoding="utf-8") as file_handle:
                contents = file_handle.read()
            return f"=== Contents of '{target_path}' ===\n\n{contents}"
        except PermissionError:
            return f"Error: Permission denied reading '{target_path}'."
        except UnicodeDecodeError:
            return f"Error: Cannot read '{target_path}' - file may not be plain text."
        except OSError as error:
            return f"Error reading file '{target_path}': {error}"

    def _write_file(self, safe_name: str, content: str) -> str:
        if not content:
            return "Error: 'content' is required when action is 'write'."

        name_only = os.path.splitext(safe_name)[0]
        if name_only == "":
            return "Error: Invalid filename."

        output_name = f"{name_only}.txt"
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(self.OUTPUT_DIR, output_name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_content = f"Saved by AI Assistant - {timestamp}\n{'=' * 40}\n\n{content}"

        try:
            with open(file_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(full_content)
            return f"File saved successfully: '{file_path}'"
        except PermissionError:
            return f"Error: Permission denied writing to '{file_path}'."
        except OSError as error:
            return f"Error saving file: {error}"

    def get_declaration(self) -> dict[str, Any]:
        """Return the Gemini function declaration for unified file operations."""
        return {
            "name": "file_manager",
            "description": (
                "Read or write local text files. Use action='read' to read a local file and "
                "action='write' to save text into saved_outputs as a .txt file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Operation type: 'read' or 'write'.",
                        "enum": ["read", "write"],
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Filename to read or write (e.g. notes.txt or summary).",
                    },
                    "content": {
                        "type": "string",
                        "description": "Required when action is 'write'. Full text to save.",
                    },
                },
                "required": ["action", "file_path"],
            },
        }
