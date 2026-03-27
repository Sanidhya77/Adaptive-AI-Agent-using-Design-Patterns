"""Document analyzer tool for PDF and text files."""

from __future__ import annotations

import base64
import os
from typing import Any

from google import genai
from google.genai import types

from tools.base_tool import BaseTool


class DocumentAnalyzerTool(BaseTool):
    """
    This is Custom Tool 1. It reads local PDF or TXT files and asks Gemini questions about them.
    It returns a valid JSON schema declaration.
    It handles errors properly if the file is too big or missing.
    """

    SUPPORTED_EXTENSIONS: set[str] = {".pdf", ".txt", ".md"}
    MAX_FILE_SIZE_BYTES: int = 10_000_000
    MIME_TYPES: dict[str, str] = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/plain",
    }

    def execute(self, file_path: str, question: str = "Summarize this document") -> str:
        """Read a document and ask Gemini a question about its contents.

        Args:
            file_path: Path or filename of the document to analyze.
            question: Question asked about the document. Defaults to summary.

        Returns:
            The analysis result or a clear error string.
        """
        safe_name = os.path.basename(file_path)
        if safe_name == "":
            return "Error: Invalid file path."

        extension = os.path.splitext(safe_name)[1].lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            return (
                f"Error: Unsupported file type '{extension}'. "
                f"Supported: {self.SUPPORTED_EXTENSIONS}"
            )

        candidate_paths = [safe_name, os.path.join("saved_outputs", safe_name)]
        target_path = next((path for path in candidate_paths if os.path.exists(path)), None)
        if not target_path:
            return f"Error: File '{safe_name}' not found in project root or 'saved_outputs'."

        if os.path.getsize(target_path) > self.MAX_FILE_SIZE_BYTES:
            return "Error: File too large. Maximum size is 10MB."

        try:
            with open(target_path, "rb") as file_handle:
                file_bytes = file_handle.read()
            encoded = base64.standard_b64encode(file_bytes).decode("utf-8")
            mime_type = self.MIME_TYPES[extension]

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return "Error: GEMINI_API_KEY is not set in environment."

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type=mime_type,
                                    data=encoded,
                                )
                            ),
                            types.Part(text=question),
                        ]
                    )
                ],
            )
            return response.text or "No response text received from document analysis."
        except FileNotFoundError:
            return f"Error: File '{safe_name}' not found in project root or 'saved_outputs'."
        except PermissionError:
            return f"Error: Permission denied reading '{target_path}'."
        except Exception as error:
            return f"Document analysis error: {str(error)}"

    def get_declaration(self) -> dict[str, Any]:
        """Return Gemini declaration for document analysis tool."""
        return {
            "name": "document_analyzer",
            "description": (
                "Reads a PDF or text document from the local filesystem and answers "
                "questions about its contents using AI analysis. Use this when the "
                "user uploads or mentions a document file (.pdf, .txt, .md) and wants "
                "to ask questions about it, get a summary, extract information, or "
                "analyze its contents."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path or filename of the document. e.g. 'report.pdf' or 'notes.txt'",
                    },
                    "question": {
                        "type": "string",
                        "description": "The question to ask about the document. Defaults to summarizing.",
                    },
                },
                "required": ["file_path"],
            },
        }
