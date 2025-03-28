"""
Simple example demonstrating direct use of the firecrawl MCP tool.
"""

import os
import asyncio
import json
from typing import Dict, Any

from dotenv import load_dotenv
import yaml
import openai

from agents_mcp import Agent, RunnerContext
from agents import Runner

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
# Force set OPENAI_API_KEY in environment for SDK trace export
if openai.api_key:
    os.environ["OPENAI_API_KEY"] = openai.api_key


# URL to scrape
EXAMPLE_URL = "https://example.com"

async def test_firecrawl_direct():
    """Test direct use of the firecrawl_scrape tool."""
    print("\n=== TESTING FIRECRAWL SCRAPE TOOL ===")

    # Get the absolute path to the simplified config file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "mcp_agent.config.yaml")

    # Create a context with the config path
    context = RunnerContext(mcp_config_path=config_path)

    # Create an agent with minimal instructions focused on using the tool directly
    agent = Agent(
        name="Firecrawl Demo",
        instructions='''
        You are a helpful agent that summarizes all rental listings from a given URL and their details.

        1. Use firecrawl_scrape to extract rental listings from the overview page, using the following parameters:
           - formats: ["extract"]
           - onlyMainContent: true
           - extract:
               schema:
                 type: object
                 properties:
                   listings:
                     type: array
                     items:
                       type: object
                       properties:
                         title:
                           type: string
                         price:
                           type: string
                         location:
                           type: string
                         bedrooms:
                           type: integer
                         bathrooms:
                           type: integer
                         lease_duration:
                           type: string
                         description:
                           type: string
                         url:
                           type: string
                       required: [title, price, location, bedrooms, bathrooms, lease_duration, description, url]
                 required: [listings]
               prompt: "Extract rental listing details, including title, price, location, number of bedrooms and bathrooms, lease duration, full description, and listing URL."
               systemPrompt: "You are extracting structured data from rental listings."

        2. List all listings. Do not skip or summarize with “and so on.” in summary form
        3. Avoid disclaimers or filler text. Return only the structured info in a clean readable list.
    ''',
        mcp_servers=["mcp-server-firecrawl"]
    )


    try:
        
        # print("Agent instructions:")
        # print(agent.instructions)

        print("\n=== Preparing to run tool with input ===")
        print(f"Input: Use the firecrawl_scrape tool to scrape this URL: {EXAMPLE_URL}")


        # Run the agent with a direct instruction to use the tool

        try:
            result = await asyncio.wait_for(Runner.run(
                agent,
                input=f"Use the firecrawl_scrape tool to scrape this URL: {EXAMPLE_URL}",
                context=context
            ), timeout=30)
        except asyncio.TimeoutError:
            print("\n=== TIMEOUT: Runner.run() did not complete in 30 seconds ===")
            return


        print("\n=== RAW RESULT DUMP ===")
        print(f"Type: {type(result)}")

        try:
            print("final_output:", getattr(result, "final_output", "<no final_output>"))
            print("raw output:", result)
            print("trace:", getattr(result, "trace", "<no trace>"))
            print("response:", getattr(result, "response", "<no response>"))
        except Exception as e:
            print("Failed to unpack result:", e)


        if result is None:
            print("Runner returned None")
        elif hasattr(result, 'final_output'):
            print("Final output:")
            print(result.final_output)
        else:
            print("Runner result has no final_output field. Dumping raw JSON:")
            print(json.dumps(result.__dict__, indent=2, default=str))


        print(f"\n=== FIRECRAWL TOOL RESULT ===")
        print(result.final_output)

        # Also show debug metadata if available
        if hasattr(result, "trace") and result.trace:
            print("\n=== DEBUG TRACE ===")
            print(json.dumps(result.trace, indent=2))

        return result.final_output

    except Exception as e:
        print("\n=== ERROR OCCURRED ===")
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run the example."""
    await test_firecrawl_direct()

if __name__ == "__main__":
    asyncio.run(main())