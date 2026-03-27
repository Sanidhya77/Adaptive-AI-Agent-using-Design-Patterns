"""Gemini ReAct agent orchestration."""

from __future__ import annotations

from google import genai
from google.genai import types
from google.genai.errors import APIError

from memory_manager import MemoryManager
from tool_registry import ToolRegistry


class Agent:
    """
    This class talks to Gemini and runs the Reason -> Act -> Observe loop.
    It follows SRP because it only controls the agent loop, not memory or tools.
    It follows DIP because it uses ToolRegistry and MemoryManager interfaces instead of hardcoding them.
    """

    def __init__(self, api_key: str, registry: ToolRegistry, memory: MemoryManager) -> None:
        """Initialize Gemini client and wire runtime dependencies.

        Args:
            api_key: Gemini API key.
            registry: Dynamic tool registry.
            memory: Conversation memory store.
        """
        self._client = genai.Client(api_key=api_key)
        self._registry = registry
        self._memory = memory
        self._model = "gemini-2.5-flash"
        self._system_prompt = (
            "You are a helpful personal assistant. "
            "You have access to tools for calculations, checking time, weather, "
            "file operations (read/write), and document analysis. Use tools whenever the user's "
            "request requires real data or actions. "
            "Use conversation history to answer follow-up questions that refer "
            "to previous turns (for example: 'the cities you listed before'). "
            "If the user asks for previously provided data, answer from memory "
            "unless they explicitly request fresh/live values. Think step by step."
        )
        self._max_tool_steps = 6

        self._tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(**declaration)
                    for declaration in registry.get_declarations()
                ]
            )
        ]
        self._config = types.GenerateContentConfig(
            system_instruction=self._system_prompt,
            tools=self._tools,
        )

    def chat(self, user_input: str) -> str:
        """Execute the ReAct loop for one user turn.

        1. REASON: Send memory to Gemini and receive candidate response parts.
        2. ACT: If a function call is present, execute via ToolRegistry.
        3. OBSERVE: Add tool result to memory and continue looping.
        4. Return final text when Gemini responds without further function calls.

        Args:
            user_input: Latest user message.

        Returns:
            Final assistant text or a clean error string.
        """
        self._memory.add_message("user", user_input)

        for _ in range(self._max_tool_steps):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=self._memory.get_history(),
                    config=self._config,
                )
            except APIError as error:
                return f"Gemini API error: {getattr(error, 'message', str(error))}"
            except Exception as error:
                return f"Unexpected error contacting Gemini: {str(error)}"

            if not response.candidates:
                return "No response from Gemini. Please try again."

            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                return "Response was blocked or empty. Please rephrase."

            parts = candidate.content.parts
            function_calls = [part.function_call for part in parts if part.function_call]

            if function_calls:
                for function_call in function_calls:
                    tool_name = function_call.name or ""
                    raw_args = function_call.args or {}
                    tool_args = dict(raw_args) if isinstance(raw_args, dict) else {}

                    info_icons = {
                        "calculator": "🧮",
                        "get_current_time": "🕐",
                        "get_weather": "🌤️",
                        "file_manager": "🗂️",
                        "document_analyzer": "📄",
                    }
                    icon = info_icons.get(tool_name, "🔧")
                    print(f"\r  {icon} Using: {tool_name}...", flush=True)

                    tool_result = self._registry.execute(tool_name, **tool_args)

                    self._memory.add_message(
                        "model",
                        f"[Calling tool: {tool_name} with args: {tool_args}]",
                    )
                    self._memory.add_message(
                        "model",
                        f"[Tool result from {tool_name}]: {tool_result}",
                    )
                continue

            text_parts = [part.text for part in parts if part.text]
            if text_parts:
                final_answer = "\n".join(text_parts)
                self._memory.add_message("model", final_answer)
                return final_answer
            return "I couldn't generate a response. Please try again."

        return "I reached the tool-step limit for this request. Please rephrase and try again."
