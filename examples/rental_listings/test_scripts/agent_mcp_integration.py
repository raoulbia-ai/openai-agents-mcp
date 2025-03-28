import os
import asyncio
from dotenv import load_dotenv
import openai
from agents_mcp import Agent, RunnerContext
from agents import Runner
from mcp_agent.config import MCPSettings

# === Load environment ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY is not set")

# === Constants ===
URL = os.getenv("WEBSITE_URL", "https://www.daft.ie/property-for-rent/clontarf-dublin?numBeds_from=2&numBeds_to=2&rentalPrice_to=2500")

# === MCP Setup ===
mcp_config = MCPSettings(
    servers={
        "mcp-server-firecrawl": {
            "command": "node",
            "args": [
                "C:\\Users\\RaoulBiagioni\\Documents\\repos\\repo-mcp-firecrawl\\dist\\index.js"
            ],
            "env": {
                "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "your-fallback-api-key")
            }
        }
    }
)
context = RunnerContext(mcp_config=mcp_config)

# === Agent Setup ===
agent = Agent(
    name="Rental Listings Agent",
    instructions=f'''
        You are a helpful agent that summarizes all rental listings from a given page and their details.

        1. Use firecrawl_scrape to extract links to all individual listings from the overview page.
        2. Follow every link and scrape relevant information. Only return the relevant information.
        3. For each listing, extract and summarise the following details:
        - title
        - price
        - location
        - number of bedrooms
        - number of bathrooms
        - lease duration (e.g., "Minimum 1 Year")
        - full description
        - listing url
        4. List all listings. Do not skip or summarize with “and so on.” in summary form
        5. Avoid disclaimers or filler text. Return only the structured info in a clean readable list.
''',
    tools=[],
    mcp_servers=["mcp-server-firecrawl"],
    model="gpt-4"
)   

# === Run ===
async def main():
    print(f"\n🔎 Scraping rentals from: {URL}")
    try:
        result = await asyncio.wait_for(
            Runner.run(
                agent,
                input=f"Scrape rental listings from {URL}",
                context=context
            ),
            timeout=600
        )
        print("\n📋 Final Output:\n")
        print(result.final_output)
    except asyncio.TimeoutError:
        print("\n❌ Timeout: Took too long.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
