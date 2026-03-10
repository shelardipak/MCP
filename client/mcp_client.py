import asyncio
import os
import json
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path
import requests
import uuid
from dotenv import load_dotenv

# Load environment variables
script_dir = Path(__file__).resolve().parent
env_path = script_dir.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def mcp_linting_flow():
    # Read the code to analyze
    with open("sample-code/bad_code.py", "r") as f:
        code_to_analyze = f.read()

    print("="*70)
    print("MCP-BASED LINTER")
    print("="*70)
    print("\nConnecting to MCP server...\n")

    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["server/mcp_server.py"],
        env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()

                # Get available tools from MCP server
                tools_list = await session.list_tools()
                print(f"✓ Connected to MCP server")
                print(f"✓ Available tools in MCP server: {[tool.name for tool in tools_list.tools]}\n")

                # Send available tools to LLM for selection
                tool_selection_prompt = [
                    {
                        "role": "user",
                        "content": (
                            "The following tools are available for linting:\n"
                            f"{[tool.name for tool in tools_list.tools]}\n\n"
                            "Please respond with the name of the most appropriate tool for analyzing Python code. "
                            "Only provide the tool name as the response."
                        )
                    }
                ]

                uri = 'https://api-dev1.mandg.co.uk/enterprise/azureopenai/openai/v1/chat/completions'
                api_key = os.getenv("OPENAI_API_KEY")
                correlation_id = str(uuid.uuid4())
                headers = {
                    'X-GenCore-Correlation-ID': correlation_id,
                    'api-key': api_key,
                    'Content-Type': 'application/json'
                }
                body = {
                    'messages': tool_selection_prompt,
                    'temperature': 0,
                    'model': 'gpt-4.1'
                }
                response = requests.post(uri, headers=headers, json=body)
                tool_selection_response = response.json()

                # Extract and validate the selected tool
                selected_tool = tool_selection_response['choices'][0]['message']['content'].strip()
                print(f"\n✓ LLM selected tool: {selected_tool}\n")

                if selected_tool not in [tool.name for tool in tools_list.tools]:
                    raise ValueError(
                        f"Selected tool '{selected_tool}' is not available on the MCP server. "
                        f"Available tools: {[tool.name for tool in tools_list.tools]}"
                    )

                print("="*70)
                print("STEP 2: Executing selected linter tool on MCP server")
                print("="*70)

                # Load custom rules from rules_config.json
                rules_config_path = script_dir.parent / "server" / "rules_config.json"
                with open(rules_config_path, "r") as rules_file:
                    custom_rules = json.load(rules_file)

                print("Loaded custom rules:", custom_rules)

                # Execute the selected tool via MCP with custom rules
                lint_result = await session.call_tool(selected_tool, {
                    "code": code_to_analyze,
                    "rules": custom_rules
                })

                print("\n✓ Linter tool executed successfully")
                print("\nRaw linting results:")
                print("-" * 70)
                print(lint_result.content[0].text)
                print("-" * 70)

                # Second call: Refine linting results using LLM
                refinement_prompt = [
                    {
                        "role": "user",
                        "content": f"The linter tool '{selected_tool}' analyzed the code and returned the following results:\n\n{lint_result.content[0].text}\n\nPlease provide a detailed explanation of the issues and suggestions for improvement.Please give output in nice json format with keys 'line','issue','rule', 'explanation', and 'suggestion'."
                    }
                ]

                uri = 'https://api-dev1.mandg.co.uk/enterprise/azureopenai/openai/v1/chat/completions'
                api_key = os.getenv("OPENAI_API_KEY")
                correlation_id = str(uuid.uuid4())
                headers = {
                    'X-GenCore-Correlation-ID': correlation_id,
                    'api-key': api_key,
                    'Content-Type': 'application/json'
                }
                body = {
                    'messages': refinement_prompt,
                    'temperature': 0,
                    'model': 'gpt-4.1'
                }
                refinement_response = requests.post(uri, headers=headers, json=body)
                refinement_response = refinement_response.json()

                print("="*70)
                print("STEP 3: Refining linting results with LLM")
                print("="*70)
                print(refinement_response['choices'][0]['message']['content'])
    except Exception as e:
        import anyio
        if isinstance(e, anyio.BrokenResourceError):
            print("[ERROR] The connection to the MCP server was unexpectedly closed (BrokenResourceError). Please check if the server is running and reachable.")
        else:
            print(f"[ERROR] An unexpected exception occurred: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(mcp_linting_flow())
