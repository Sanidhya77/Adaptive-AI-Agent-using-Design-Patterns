"""Interactive CLI entry point for the AI personal assistant."""

from __future__ import annotations

import os
import shutil
import sys
import textwrap

from dotenv import load_dotenv

from agent import Agent
from memory_manager import MemoryManager
from tool_registry import ToolRegistry

TOOL_INFO: dict[str, dict[str, str]] = {
    "calculator": {
        "icon": "🧮",
        "label": "Calculator",
        "hint": "e.g. 'What is 15% of 340?'",
    },
    "get_current_time": {
        "icon": "🕐",
        "label": "Current Time & Date",
        "hint": "e.g. 'What time is it in Tokyo?'",
    },
    "get_weather": {
        "icon": "🌤️",
        "label": "Weather Lookup",
        "hint": "e.g. 'What is the weather in Berlin?'",
    },
    "file_manager": {
        "icon": "🗂️",
        "label": "File Manager (Read/Write)",
        "hint": "e.g. 'Read notes.txt' or 'Save this as summary'",
    },
    "document_analyzer": {
        "icon": "📄",
        "label": "Document Analyzer (PDF/TXT)",
        "hint": "e.g. 'Summarize report.pdf' or 'What does this document say about X?'",
    },
}


def _declaration_to_label(tool_name: str, description: str) -> str:
    """Build a readable label from tool declaration data."""
    if tool_name in TOOL_INFO:
        return TOOL_INFO[tool_name]["label"]

    cleaned_name = tool_name.replace("_", " ").title()
    return cleaned_name if cleaned_name else description[:32]


def _declaration_to_hint(description: str) -> str:
    """Generate a short hint from declaration description when no static hint exists."""
    compact = " ".join(description.split())
    return compact[:90] + ("..." if len(compact) > 90 else "")


def handle_upload_command(user_input: str) -> str | None:
    """Process: upload <path>. Returns status text when command was handled."""
    if not user_input.lower().startswith("upload "):
        return None

    raw_path = user_input[7:].strip().strip('"').strip("'")
    if not raw_path:
        return "  ❌ Usage: upload <path_to_file>"

    if not os.path.isfile(raw_path):
        return f"  ❌ File not found: {raw_path}"

    os.makedirs("saved_outputs", exist_ok=True)
    destination = os.path.join("saved_outputs", os.path.basename(raw_path))
    try:
        shutil.copy2(raw_path, destination)
        return f"  ✅ Uploaded to: {destination}"
    except PermissionError:
        return "  ❌ Permission denied while uploading file."
    except OSError as error:
        return f"  ❌ Upload failed: {error}"


def print_banner() -> None:
    """Print the app banner."""
    print("=" * 60)
    print("           🤖  AI PERSONAL ASSISTANT")
    print("        Powered by Google Gemini 2.5 Flash")
    print("=" * 60)
    print()


def print_usage_guide() -> None:
    """Print a complete in-CLI guide for operating the assistant."""
    print("  QUICK START:")
    print("  1) Ask questions naturally (the agent decides when to use tools).")
    print("  2) Use 'upload <path>' to copy local files into saved_outputs.")
    print("  3) Ask to summarize or analyze uploaded files by filename.")
    print("  4) Ask to save the chat response (e.g., 'save this answer as notes.txt').")
    print()
    print("  EXAMPLES:")
    print("  • 'What is the weather in Riga?'")
    print("  • 'What time is it in Europe/Riga?'")
    print("  • 'Calculate (24*18)/3' or 'What is 15% of 340?'")
    print("  • 'Save this summary to a file called project_notes'")
    print("  • 'Read project_notes.txt'")
    print("  • 'Summarize report.pdf' or 'What are key points in report.pdf?'")
    print()
    print("  FILE ANALYSIS NOTES:")
    print("  • Terminal CLI does not support drag-and-drop file upload.")
    print("  • Use: upload C:\\path\\to\\your\\file.pdf")
    print("  • Analyzer searches file in project root and saved_outputs.")
    print()


def print_tool_menu(registry: ToolRegistry) -> None:
    """Print all available tools and CLI commands."""
    declaration_map = {decl["name"]: decl for decl in registry.get_declarations()}

    print("  AVAILABLE TOOLS:")
    print("  " + "-" * 58)
    for index, tool_name in enumerate(registry.list_tools(), start=1):
        declaration = declaration_map.get(tool_name, {})
        description = declaration.get("description", "")

        # Fallback label/hint comes from declarations so new tools show useful info
        # even if TOOL_INFO is not manually updated.
        info = TOOL_INFO.get(
            tool_name,
            {
                "icon": "🔧",
                "label": _declaration_to_label(tool_name, description),
                "hint": _declaration_to_hint(description),
            },
        )
        print(f"  [{index}] {info['icon']}  {info['label']}")
        print(f"       {info['hint']}")
    print("  " + "-" * 58)
    print()
    print("  COMMANDS:")
    print("  • Type naturally - the agent picks the right tool automatically")
    print("  • 'help'   -> show full usage guide")
    print("  • 'upload <path>' -> copy a file into saved_outputs for analysis")
    print("  • 'tools'  -> show this tool list again")
    print("  • 'clear'  -> reset conversation memory")
    print("  • 'exit'   -> quit")
    print("=" * 60)
    print()


def print_thinking_indicator() -> None:
    """Show a one-line thinking indicator while waiting for response."""
    print("  ⏳ Thinking...", end="", flush=True)


def print_tool_used(tool_name: str) -> None:
    """Print which tool is being used.

    Args:
        tool_name: Tool name selected by the model.
    """
    info = TOOL_INFO.get(tool_name, {"icon": "🔧", "label": tool_name})
    print(f"\n  {info['icon']} Using tool: {info['label']}...")


def main() -> None:
    """Run the interactive CLI application."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print_banner()
        print("  ❌ ERROR: GEMINI_API_KEY not found in .env file")
        print("  Create a .env file and add: GEMINI_API_KEY=your_key_here")
        print("  Get a free key at: https://aistudio.google.com")
        sys.exit(1)

    registry = ToolRegistry()
    discovered_tools = registry.auto_register_from_package("tools")
    if not discovered_tools:
        print("  ❌ ERROR: No tools discovered. Check the tools package.")
        sys.exit(1)

    memory = MemoryManager()
    agent = Agent(api_key=api_key, registry=registry, memory=memory)

    print_banner()
    print_usage_guide()
    print_tool_menu(registry)

    while True:
        try:
            turn = memory.get_turn_count()
            prompt_label = f"You (turn {turn + 1}): " if turn > 0 else "You: "
            user_input = input(prompt_label).strip()
        except KeyboardInterrupt:
            print("\n\n  👋 Goodbye!\n")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("\n  👋 Goodbye!\n")
            break

        # Quick local upload path for document analysis in terminal workflows.
        upload_status = handle_upload_command(user_input)
        if upload_status is not None:
            print(f"\n{upload_status}\n")
            continue

        if user_input.lower() == "clear":
            memory.clear()
            print("\n  🗑️  Memory cleared. Starting fresh.\n")
            print_tool_menu(registry)
            continue

        if user_input.lower() == "tools":
            print()
            print_tool_menu(registry)
            continue

        if user_input.lower() == "help":
            print()
            print_usage_guide()
            print_tool_menu(registry)
            continue

        print_thinking_indicator()
        response = agent.chat(user_input)

        print("\r" + " " * 20 + "\r", end="")
        print("\n  🤖 Assistant:\n")

        wrapped = textwrap.fill(
            response,
            width=70,
            initial_indent="  ",
            subsequent_indent="  ",
        )
        print(wrapped)
        print()


if __name__ == "__main__":
    main()
