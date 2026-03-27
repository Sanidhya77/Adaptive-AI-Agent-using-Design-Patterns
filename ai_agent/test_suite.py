import os
import sys
from dotenv import load_dotenv

from agent import Agent
from memory_manager import MemoryManager
from tool_registry import ToolRegistry

def print_test_separator(title="TEST"):
    print(f"\n{'-'*60}")
    print(f" {title}")
    print(f"{'-'*60}\n")

def run_tests():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env. Test cannot proceed.")
        sys.exit(1)
        
    registry = ToolRegistry()
    registry.auto_register_from_package("tools")
    
    memory = MemoryManager()
    agent = Agent(api_key=api_key, registry=registry, memory=memory)
    
    # 1. Test basic calculator and time
    print_test_separator("Test 1: Multiple Basic Tools (Calculator + Time)")
    query = "What time is it in Tokyo right now? Also what is 14450 divided by 25?"
    print(f"User: {query}")
    print(f"Agent:\n{agent.chat(query)}")
    
    # 2. Test File Manager (Write)
    print_test_separator("Test 2: Custom Tool - File Manager (Write)")
    query = "Save a small note saying 'The multi-tool integration test works perfectly' into a file named 'test_note'."
    print(f"User: {query}")
    print(f"Agent:\n{agent.chat(query)}")
    
    # 3. Test File Manager (Read) + Document Analyzer
    # Wait, document analyzer needs a PDF or TXT. We just created test_note.txt.
    print_test_separator("Test 3: Custom Tool - Document Analyzer")
    query = "Read the contents of the 'test_note.txt' document explicitly using your document analyzer tool and tell me what it says."
    print(f"User: {query}")
    print(f"Agent:\n{agent.chat(query)}")
    
    # 4. Error Handling
    print_test_separator("Test 4: Error Handling (Missing File)")
    query = "Try to analyze the document 'this_file_does_not_exist_at_all.pdf'."
    print(f"User: {query}")
    print(f"Agent:\n{agent.chat(query)}")
    
    print("\n✅ Verification complete.")

if __name__ == "__main__":
    run_tests()
