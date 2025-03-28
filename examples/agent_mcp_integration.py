# OpenAI Agent SDK & MCP Example: Rental Listings Orchestration
#
# This script demonstrates orchestrating multiple AI agents using the OpenAI Agent SDK (`agents` library)
# and its Model Context Protocol (MCP) extension (`openai-agents-mcp`)
# to automate the process of finding rental listings and notifying users.
#
# Key Concepts Illustrated:
# - Agent Definition: Defining specialized agents (`ListingURLsAgent`, `IndividualListingAgent`, `EmailMetadataAgent`, `OrchestratorAgent`)
#   using both the core `agents.Agent` and MCP-enabled `agents_mcp.Agent` classes.
# - `openai-agents-mcp` Library: This companion library provides the `MCPAgent` class and `RunnerContext`
#   necessary for agents to interact with external tools and resources via the Model Context Protocol.
# - Model Context Protocol (MCP): Utilizing an MCP server (`mcp-server-firecrawl`) to provide external tools (web scraping via Firecrawl API)
#   to agents (`ListingURLsAgent`, `IndividualListingAgent`). The `RunnerContext` manages MCP connections.
# - Agent Orchestration: An `OrchestratorAgent` coordinates the workflow, calling other agents as tools (`as_tool`).
# - Function Tools: Integrating standard Python functions (`send_formatted_email_tool`) as tools for agents using the `@function_tool` decorator.
# - Structured Output: Using Pydantic models (`ListingItem`, `EmailMetadata`, `EmailPayload`) to define and enforce schemas for agent outputs and tool inputs/outputs.
# - Error Handling: Demonstrates basic error handling within the orchestration logic (logging failed scrapes).
# - Environment Variables: Using `.env` for managing sensitive API keys (OpenAI, Firecrawl, Gmail).
# - Tracing: Integration with the SDK's tracing capabilities (`TraceProvider`).
#
# SDK vs MCP Extension Usage in this Script:
#   - Core SDK (`agents`):
#     - `Agent`: Used for `email_payload_agent` and `orchestrator_agent`.
#     - `Runner`: Used in `main()` to execute the `orchestrator_agent`.
#     - `@function_tool`: Decorator for `send_formatted_email_tool`.
#     - `RunConfig`, `ModelSettings`: Used to configure the agent run in `main()`.
#     - `.as_tool()`: Used by `orchestrator_agent` to wrap other agents.
#   - MCP Extension (`agents_mcp`):
#     - `MCPAgent`: Used for `listing_urls_agent` and `individual_listing_agent` to enable MCP tool usage.
#     - `RunnerContext`: Used to create the `context` variable, configuring the connection to the `mcp-server-firecrawl`.

import os
import re
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, RunConfig, ModelSettings # Removed RunContextWrapper
from agents_mcp import Agent as MCPAgent, RunnerContext
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from agents.tracing.setup import TraceProvider  # Changed import
import time
from markdown import markdown

# Load environment variables
load_dotenv()

from agents import set_tracing_export_api_key
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

# Load Gmail credentials globally
gmail_user = os.getenv("GMAIL_USER")
gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

# Initialize trace provider
trace_provider = TraceProvider()  # Create trace provider instance

# --- Pydantic Models for Structured Output ---
class ListingItem(BaseModel):
    title: Optional[str] = None
    price: Optional[str] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    lease: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    url: Optional[str] = None

class EmailMetadata(BaseModel): # Renamed from EmailPayload
    recipient: str
    subject: str
    # Removed listings field

class EmailPayload(BaseModel):
    recipient: str
    subject: str
    listings: List[ListingItem]

# --- MCP Setup ---
mcp_config = {
    "servers": {
        "mcp-server-firecrawl": {
            "command": "node",
            "args": [
                # Adjust this path to your Firecrawl MCP server location if different
                "C:\\Users\\RaoulBiagioni\\Documents\\repos\\repo-mcp-firecrawl\\dist\\index.js"
            ],
            "env": {
                "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY")
            }
        }
    }
}
context = RunnerContext(mcp_config=mcp_config)

# --- Listing URLs Agent ---
listing_urls_agent = MCPAgent(
    name="ListingURLsAgent",
    instructions='''
    You are extracting URLs of rental listings from a main page.
    
    First, extract the URL from the input parameter. If the input is a string, use it directly.
    If the input is an object with an "input" property, use the value of that property.
    
    Then use firecrawl_scrape tool (not any other firecrawl tool) with these parameters:
    {
        "url": "[extracted_url]",
        "formats": ["extract"],
        "onlyMainContent": true,
        "timeout": 30000,
        "extract": {
            "schema": {
                "type": "object",
                "properties": {
                    "listings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "The full URL of the individual rental listing page."
                                }
                            },
                            "required": ["url"]
                        }
                    }
                },
                "required": ["listings"]
            },
            "systemPrompt": "You are an expert web scraper. Your task is to identify and extract the URLs that link directly to individual rental property listings from the provided HTML content. Focus only on links that represent specific properties for rent.",
            "prompt": "Extract all individual rental listing URLs from the page content. Return them as a JSON object following the provided schema."
        }
    }
    
    Process the JSON output from the scrape tool. Extract the URL from each item in the 'listings' array.
    Return the extracted URLs as a clean list, one URL per line. Ensure only valid URLs are returned.
    ''',
    tools=[],
    mcp_servers=["mcp-server-firecrawl"],
    model="gpt-4o"
)

# --- Individual Listing Agent ---
individual_listing_agent = MCPAgent(
    name="IndividualListingAgent",
    instructions='''
    You are extracting key information from individual rental listing pages.
    
    IMPORTANT: The input to this agent is a specific listing URL. Make sure to:
    1. Include the original listing URL in your response as the "url" field 
    2. Use this exact URL in your scraping request
    
    Use the firecrawl_scrape tool (not any other firecrawl tool) with these parameters:
    {
        "url": "[listing_url]",
        "formats": ["extract"],
        "onlyMainContent": true,
        "timeout": 30000,
        "extract": {
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "price": {"type": "string"},
                    "location": {"type": "string"},
                    "bedrooms": {"type": "integer"},
                    "bathrooms": {"type": "integer"},
                    "lease": {"type": "string"}, 
                    "description": {"type": "string"},
                    "contact_email": {"type": "string"},
                    "url": {"type": "string", "description": "The FULL URL of this specific listing page (use the exact input URL)"}
                },
                "required": ["title", "price", "location", "url"]
            },
            "prompt": "Extract key rental listing details including title, price, location, bedrooms, bathrooms, lease duration (as 'lease'), contact email (as 'contact_email'), provide a concise summarized description. IMPORTANT: Include the original full listing URL in the 'url' field."
        }
    }
    
    FINAL STEP: After extracting the data, make absolutely sure the 'url' field contains the FULL, EXACT original listing URL that was passed to this agent.
    
    Return the extracted data as a JSON object conforming to the schema. Do not add any extra text.
    ''',
    tools=[],
    mcp_servers=["mcp-server-firecrawl"],
    model="gpt-4o",
    output_type=ListingItem # Ensure output matches Pydantic model
)

email_payload_agent = Agent( 
    name="EmailMetadataAgent",
    instructions='''You are an agent that determines the recipient email addresses and subject line for a rental listings summary email.

    Your task is to create a JSON object conforming to the EmailMetadata schema.
    - Always use "YOUR_EMAIL_1@example.com,YOUR_EMAIL_2@example.com" as the recipient email addresses (comma-separated).
    - Always use "Rental Listings Update" as the subject line.

    Respond ONLY with the valid JSON object matching the EmailMetadata schema. Do not include any other text.
    ''',
    output_type=EmailMetadata,
    model="gpt-4o",
    model_settings=ModelSettings(temperature=0) # Properly initialized ModelSettings object
    # No tools needed for this agent
)


@function_tool
def send_formatted_email_tool(
    listings_data: List[ListingItem],
) -> str:

    """
    Formats rental listings from data, then sends the email.
    Args:
        listings_data: A list of dictionaries, where each dictionary represents a ListingItem.
    """
    try:
        # --- Construct EmailPayload internally ---
        # Validate/parse listings data
        validated_listings = [ListingItem.model_validate(item) for item in listings_data]
        
        # Create the payload object with placeholder values
        # Using a comma-separated list for multiple recipients
        payload = EmailPayload(
            recipient="YOUR_EMAIL_1@example.com,YOUR_EMAIL_2@example.com", # Placeholder emails
            subject="Rental Listings Update",
            listings=validated_listings
        )
    except Exception as e:
        error_msg = f"Error constructing email payload from input data: {str(e)}"
        print(error_msg)
        return error_msg

    # --- Deterministic Formatting Logic (uses the constructed 'payload' object) ---
    body_lines = []
    body_lines.append(f"Hello,\n")
    body_lines.append(f"Here are the latest rental listings:\n")

    if not payload.listings:
        body_lines.append("No new listings found this time.")
    else:
        for item in payload.listings:
            line_parts = []
            if item.title:
                line_parts.append(f"\n**{item.title}**")
            if item.price:
                line_parts.append(f"\n{item.price}")
            if item.location:
                line_parts.append(f"\n{item.location}")
            if item.bedrooms is not None:
                 line_parts.append(f"\n{item.bedrooms} Bed")
            if item.bathrooms is not None:
                 line_parts.append(f"\n{item.bathrooms} Bath")
            if item.lease:
                 line_parts.append(f"\nLease: {item.lease}")

            # Join main parts with ' – '
            line = " – ".join(filter(None, line_parts))
            line = f"- {line}"

            # Add description and contact on new lines if they exist
            desc_lines = []
            if item.description:
                 # Keep description brief
                 summary = (item.description[:150] + '...') if len(item.description) > 150 else item.description
                 desc_lines.append(f"\n\t  Description: {summary.strip()}")
            if item.contact_email:
                 desc_lines.append(f"\n\t  Contact: {item.contact_email}") # Note: This might still contain real emails if scraped
            if item.url:
                 # Ensure URL is complete (starts with http:// or https://)
                 listing_url = item.url
                 if not (listing_url.startswith('http://') or listing_url.startswith('https://')):
                     listing_url = 'https://' + listing_url if not listing_url.startswith('//') else 'https:' + listing_url
                 desc_lines.append(f"\n\t  [View Listing]({listing_url})") # Add URL as a separate line

            body_lines.append(line)
            if desc_lines:
                body_lines.extend(desc_lines)
            body_lines.append("") # Add a blank line between listings

    # body_lines.append("\nBest regards,")
    # body_lines.append("Rental Listings Bot")

    email_body = "\n".join(body_lines)
    email_body = markdown(email_body)
    # --- End Formatting Logic ---

    # Check for globally loaded credentials
    if not gmail_user or not gmail_app_password:
        print("Error: Gmail credentials not configured.")
        return "Error: Gmail credentials not configured in environment variables."

    # Split comma-separated recipient list
    recipients = [email.strip() for email in payload.recipient.split(',')]
    
    print(f"Sending formatted email to: {', '.join(recipients)}")
    # print(f"Subject: {payload.subject}") # Optional: print subject
    # print(f"Body:\n{email_body}") # Optional: print body for debugging

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = payload.recipient  # Keep original comma-separated format in header
    msg['Subject'] = payload.subject
    # Send as HTML
    msg.attach(MIMEText(email_body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_app_password)
        text = msg.as_string()
        # Send to all recipients
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        print(f"Formatted email sent successfully to {', '.join(recipients)}.")
        return f"Formatted email sent successfully to {', '.join(recipients)}."
    except Exception as e:
        print(f"Error sending formatted email: {str(e)}")
        return f"Error sending formatted email: {str(e)}"

# --- Orchestrator Agent ---
orchestrator_agent = Agent(
    name="OrchestratorAgent",
    instructions='''
    You coordinate the rental listing search and email process.
    
    Workflow:
    1. Use `get_listing_urls_tool` to get the list of rental listing URLs from the main page URL provided in the user query.
       - This will return a list of full, individual listing URLs.
    
    2. For each URL in the list from step 1:
       - Use `get_listing_details_tool` passing the EXACT, FULL listing URL
       - This ensures each ListingItem has the correct URL in its "url" field
       - IMPORTANT: Pass each URL individually to get_listing_details_tool
       - HANDLE ERRORS: If a particular listing fails to scrape, log the error and continue with other listings
       - Keep track of both successful listings (for the email) and failed listings (for logging)
       - Collect all the successful results into a list of ListingItem objects
    
    3. Use `create_email_payload_tool` to get the recipient email addresses and subject line (as an `EmailMetadata` object).
       - It will use placeholder emails "YOUR_EMAIL_1@example.com,YOUR_EMAIL_2@example.com".
       - It will use "Rental Listings Update" as the subject.
    
    4. Use `send_formatted_email_tool`, passing ONLY the list of SUCCESSFUL `ListingItem` objects as the `listings_data` argument.
    
    5. At the end, provide a summary of how many listings were successfully processed and how many failed.
       For failed listings, include the URL and the error message so they can be reviewed later.

    Important Guidelines:
    - Execute steps sequentially. Do not proceed to the next step until the previous one is complete.
    - When calling `create_email_payload_tool`, pass a simple string like: "Generate email metadata for rental listings"
    - Double-check that each ListingItem in your list has the correct, full URL to the specific listing
    - ERRORS: Handle errors gracefully - if a listing fails to scrape, log it and continue with others
    - The final step is calling `send_formatted_email_tool` with only the successfully processed listings.
    ''',
    tools=[
        listing_urls_agent.as_tool(
            tool_name="get_listing_urls_tool",
            tool_description="Gets all rental listing URLs from a main page URL."
        ),
        individual_listing_agent.as_tool(
            tool_name="get_listing_details_tool",
            tool_description="Gets structured detailed rental information (ListingItem) for a list of given URLs."
        ),
        email_payload_agent.as_tool( # Use the renamed agent
            tool_name="create_email_payload_tool", # New tool name
            tool_description="Structures listing details and recipient info into an EmailPayload object."
        ),
        # Note: send_formatted_email_tool is a @function_tool, added directly unlike agent-derived tools.
        send_formatted_email_tool
    ],
    model="gpt-4", # Upgraded model for better orchestration if needed
    model_settings=ModelSettings(temperature=0) # Properly initialized ModelSettings object
)

MAX_LISTINGS = 8  # Maximum number of listings to process
MAX_TOKENS = 100000  # Maximum tokens to use per run

async def main():
    # Define the search URL and placeholder email for the query
    url = "YOUR_SEARCH_URL_HERE" # Placeholder for the actual search URL
    email_address = "YOUR_EMAIL_1@example.com" # Placeholder email for query construction
    user_query = f"Find rental listings from {url} and email them to {email_address}. Limit to {MAX_LISTINGS}."
    
    run_config = RunConfig(
        model_settings=ModelSettings(max_tokens=MAX_TOKENS),
        tracing_disabled=False  # Set to True if you want to disable tracing by default
    )
    
    # --- Delete debug log file if it exists ---
    log_file_path = 'mcp_debug.log' # Assumes the log file is in the current working directory
    if os.path.exists(log_file_path):
        try:
            os.remove(log_file_path)
            print(f"Deleted existing log file: {log_file_path}")
        except OSError as e:
            print(f"Error deleting file {log_file_path}: {e}")
    # --- End of block ---

    try:
        result = await asyncio.wait_for(
            Runner.run(
                orchestrator_agent,
                input=user_query,
                context=context,
                run_config=run_config,
                max_turns=20
            ),
            timeout=600  # 10 minutes timeout
        )
        print(result.final_output)
        
        # Create log file for failed listings if mentioned in the output
        if "failed listings" in result.final_output.lower():
            with open('failed_listings.log', 'w') as log_file:
                log_file.write(f"Failed Listings Log - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write("=" * 80 + "\n\n")
                log_file.write(result.final_output)
                print("\nFailed listings have been logged to 'failed_listings.log'")
    except asyncio.TimeoutError:
        print("The operation timed out. Please try again with a smaller number of listings.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Properly shutdown tracing
        if trace_provider and hasattr(trace_provider, '_multi_processor') and hasattr(trace_provider._multi_processor, '_processors'):
            for processor in trace_provider._multi_processor._processors:
                if hasattr(processor, 'force_flush'):
                    processor.force_flush()  # Force export any remaining spans
                if hasattr(processor, 'shutdown'):
                    processor.shutdown(timeout=5.0)  # Give it 5 seconds to shutdown cleanly

if __name__ == "__main__":
    # Run the full orchestration
    print("\nRunning full orchestration...")
    asyncio.run(main())