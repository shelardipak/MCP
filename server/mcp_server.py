import asyncio
import json
import os
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from lint_engine import run_lint_analysis

# Create MCP server instance
app = Server("python-linter-mcp")

# Enable logging for debugging (optional) - use stderr since stdout is for MCP protocol
import logging
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available tools.
    In MCP, tools are exposed to the LLM as capabilities it can invoke.
    """
    return [
        Tool(
            name="analyze_python_code",
            description=(
                "Analyzes Python code for style violations, bepylist practices, and potential issues. "
                "Checks against configurable rules including line length, naming conventions, "
                "docstring requirements, and print statement usage. "
                "Returns a list of issues with line numbers, descriptions, suggestions, and severity levels."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to analyze"
                    },
                    "rules": {
                        "type": "object",
                        "description": "Optional custom rules to override defaults",
                        "properties": {
                            "max-line-length": {"type": "number"},
                            "variable-naming-style": {"type": "string"},
                            "allow-print": {"type": "boolean"},
                            "require-docstrings": {"type": "boolean"}
                        }
                    }
                },
                "required": ["code"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool execution requests from the LLM.
    This is where the actual linting happens when the LLM invokes the tool.
    """
    if name != "analyze_python_code":
        raise ValueError(f"Unknown tool: {name}")

    code = arguments.get("code", "")
    custom_rules = arguments.get("rules")

    # Run the linting analysis
    result = await run_lint_analysis(code, custom_rules)

    # Return results as TextContent for the LLM
    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
    ]

async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Graceful exit for your ^C
        pass