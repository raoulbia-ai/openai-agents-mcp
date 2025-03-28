"""
Test script for integrating MCP with an agent.
"""

import os
import asyncio

from dotenv import load_dotenv
import openai
from openai.types.responses import ResponseTextDeltaEvent

from agents_mcp import Agent, RunnerContext
from agents import Runner
from mcp_agent.config import MCPSettings

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
print(f"Using OpenAI API key: {openai.api_key[:10]}...{openai.api_key[-5:]}")


# Get the website URL from the environment or use a default
WEBSITE_URL = os.getenv(
    "WEBSITE_URL",
    "https://www.daft.ie/property-for-rent/clontarf-dublin?numBeds_from=2&numBeds_to=2&rentalPrice_to=2500",
)
print(WEBSITE_URL)


async def test_agent_with_mcp_tool():
    """Test an agent with an MCP tool for scraping listings."""
    print("\n=== TESTING AGENT WITH MCP TOOL ===")

    # Create a context with the config path
    mcp_config = MCPSettings(
        servers={
            "mcp-server-firecrawl": {
                "command": "node",
                "args":[
                    "C:\\Users\\RaoulBiagioni\\Documents\\repos\\repo-mcp-firecrawl\\dist\\index.js"
                ],
                "env": {"FIRECRAWL_API_KEY": "fc-b7eac79de7cc41c384d63f98496e3b64"},
            }
        }
    )
    context = RunnerContext(mcp_config=mcp_config)
    print(context)
    # Create an agent with the MCP server
    agent = Agent(
        name="Rental Listings Agent",
        instructions="""
        You are a helpful assistant that provides information about rental listings.
        
        When asked about listings, use the firecrawl_scrape tool to fetch data from the provided URL.
        The tool will return JSON data containing the webpage content.
        
        Extract the rental listings from the JSON data and present them in a clear, organized format.
        Include details such as price, location, and description when available.
        """,
        tools=[],
        mcp_servers=["mcp-server-firecrawl"],
        model="gpt-4-turbo",  # Use gpt-4-turbo for better JSON handling
    )

    # Run the agent
    print("Calling Runner.run_streamed with input:", f"Scrape rental listings from {WEBSITE_URL}")
    try:
        result = Runner.run_streamed(
            agent,
            input=f"Scrape rental listings from {WEBSITE_URL}",
            context=context,
        )
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)

    except Exception as e:
        print(f"An error occurred: {e}")

    print("\n=== AGENT RESULT WITH MCP TOOL ===")


async def main():
    """Run the tests."""
    await test_agent_with_mcp_tool()


if __name__ == "__main__":
    asyncio.run(main())