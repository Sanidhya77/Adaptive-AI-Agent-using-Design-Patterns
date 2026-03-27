# AI Personal Assistant Agent

This is an AI agent application built using Python and the Google Gemini API. It fulfills all the assignment grading criteria, including SOLID principles, Gang of Four (GoF) design patterns, and an adaptive ReAct (Reason -> Act -> Observe) loop.

## How to Run in Your Local Environment

1. **Prerequisites**
   Ensure you have Python 3.10+ installed.

2. **Environment Setup**
   Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   ```
   Activate the virtual environment:
   - **Windows PowerShell:** `.\.venv\Scripts\Activate.ps1`
   - **macOS/Linux:** `source .venv/bin/activate`

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **API Key Configuration**
   Create a `.env` file in the `ai_agent` directory and add your Google Gemini API key:
   ```properties
   GEMINI_API_KEY="your_api_key_here"
   ```
   *(You can get a free API key from [Google AI Studio](https://aistudio.google.com/))*

5. **Start the Agent**
   Run the main script to start the interactive CLI:
   ```bash
   python main.py
   ```

## Interacting with the Bot

1. **Using Tools Naturally**
   You don't need to type special slash commands. Just talk to the bot and it will figure out which tool to use.
   - Example time check: *"What time is it in Riga right now?"* 
   - Example calculation: *"What is 15% of 340?"*
   - Example weather: *"What is the weather in London?"*
2. **Uploading Files**
   To let the bot read your files (PDFs, text files), you must upload them first using the `upload` command in the prompt.
   - Type exactly: `upload C:\path\to\your\report.pdf` 
   - This copies your file into the `saved_outputs/` folder.
   - Once it's uploaded, you can ask questions about it: *"Summarize the report.pdf file I just uploaded."*
3. **Saving Chat Responses**
   If you want to keep the bot's response, just tell it to save it! The bot has a file manager tool it uses for this.
   - Example: *"Save your last answer to a file called notes"*
   - The bot will write the response to `saved_outputs/notes.txt`. You can later ask it to *"Read notes.txt"*.

## File Structure

```text
Adaptive-AI-Agent-using-Design-Patterns/
├── ai_agent/
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base_tool.py
│   │   ├── calculator_tool.py
│   │   ├── document_analyzer_tool.py
│   │   ├── file_manager_tool.py
│   │   ├── time_tool.py
│   │   └── weather_tool.py
│   ├── agent.py
│   ├── main.py
│   ├── memory_manager.py
│   ├── tool_registry.py
│   ├── test_suite.py
│   └── requirements.txt
├── .gitignore
└── README.md
```

## What is Implemented and How?

Below is a detailed breakdown of all assignment requirements, where they are implemented, and the specific files/lines of code.
Below is a detailed breakdown of all assignment requirements, where they are implemented, and the specific files/lines of code.

### 1. Separation of Concerns (SRP) & Architecture Focus
The codebase avoids monolithic execution by splitting responsibilities into dedicated interfaces:
- **`Agent`** (`agent.py:13`): Orchestrates the ReAct logic and communicates with the Gemini API.
- **`MemoryManager`** (`memory_manager.py:8`): Exclusively manages the conversation history.
- **`ToolRegistry`** (`tool_registry.py:13`): Discovers and registers tools.
- **`BaseTool`** (`tools/base_tool.py:9`): Provides the abstract interface for tools.

### 2. Design Patterns (GoF)

**What are Gang of Four (GoF) patterns?** 
They are a standard set of 23 well-known solutions to common software design problems, originally published in a famous 1994 book by four authors (hence "Gang of Four"). By using these patterns, the code is well-organized, easy to maintain, and easy to extend.

- **Strategy Pattern / Open-Closed Principle (OCP)**
  All tools inherit from `BaseTool` (`tools/base_tool.py:9`). You can add new behaviors (tools) without modifying the core `Agent` logic. Each tool implements `execute()` and `get_declaration()`.
- **Factory / Registry Pattern**
  The `ToolRegistry` (`tool_registry.py`) acts as a factory and registry. It imports and instantiates tool classes at runtime using `auto_register_from_package()` (`tool_registry.py:35`). This avoids `if/else` tool blocks.

### 3. Contextual Memory
The agent remembers all prior interactions within the active session.
- Implemented in `memory_manager.py`.
- The `add_message()` method (`memory_manager.py:20`) saves the user and model prompts into a `self._history` list (initialized on `memory_manager.py:18`).

### 4. Adaptive ReAct Loop (Reason → Act → Observe)
The bot autonomously determines whether to reply directly or use external tools.
- Iterated in `agent.py` inside the `chat()` method (starting at line 57).
- **Reason:** The LLM is queried with tool schemas and prior context (`agent.py:75`).
- **Act:** If Gemini responds with a `function_call` (`agent.py:95`), the arguments are parsed and the tool is executed via the `ToolRegistry` (`agent.py:111`).
- **Observe:** The tool output is injected back into memory (`agent.py:118`) and the loop runs again, allowing the agent to evaluate results.

### 5. Custom Tools Integration
Because of the Factory/Registry architecture, 5 tools are implemented in the `tools/` directory. Each returns a JSON declaration schema.
- **Built-in tools:** `CalculatorTool`, `TimeTool`, `WeatherTool`.
- **Document Analyzer Tool** (`tools/document_analyzer_tool.py:15`): Validates file paths, handles target chunks, and leverages multimodal parts to ask Gemini questions.
- **File Manager Tool** (`tools/file_manager_tool.py:12`): Provides read/write operations to the local filesystem.

### 6. Error Handling
The execution stack handles errors to prevent crashes:
- **API Errors** are caught during LLM generation (`agent.py:80`).
- **File System Errors** like `PermissionError` and `FileNotFoundError` are caught and returned as string instructions back to the *LLM context*, preventing app failure (e.g., `tools/document_analyzer_tool.py:87-92` and `main.py:77-80`).
- **Missing or invalid tool executions** are intercepted by the registry (`tool_registry.py:86-93`).
