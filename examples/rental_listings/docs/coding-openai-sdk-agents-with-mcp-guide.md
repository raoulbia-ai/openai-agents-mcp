# Creating OpenAI Agents with MCP Tools: A Developer's Guide

This guide explains how to create OpenAI agents that leverage the Model Context Protocol (MCP) to extend their capabilities with tools provided by MCP servers. This allows you to combine the power of OpenAI's language models with the functionality of external systems and APIs exposed through MCP.

## Prerequisites

*   Python 3.7+
*   An OpenAI API key
*   The `openai` and `agents-mcp` Python packages:
    ```bash
    pip install openai agents-mcp
    ```
*   One or more MCP servers configured (see the MCP documentation for details on setting up servers).

## Key Concepts

*   **Agent:** An autonomous entity powered by a large language model (LLM) that can interact with the world through tools.
*   **MCP (Model Context Protocol):** A protocol for connecting language models to external systems and data sources.
*   **MCP Server:** A server that exposes tools and resources via the MCP.
*   **Tool:** A function that an agent can call to perform a specific action, such as fetching data, interacting with an API, or manipulating files.
*   **`agents-mcp` library:** A Python library that provides an integration between the OpenAI Agent SDK and MCP.

## Steps to Create an Agent with MCP Tools

1.  **Configure MCP Servers:**

    You need to configure the MCP servers that your agent will use. This is typically done through a configuration file named `mcp_agent.config.yaml`. This file specifies the connection details for each MCP server.

    Example `mcp_agent.config.yaml`:

    ```yaml
    servers:
      fetch:
        command: "uvx"
        args: ["mcp-server-fetch"]
      filesystem:
        command: "npx"
        args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
      slack:
        command: "node"
        args: ["/path/to/slack-mcp-server/build/index.js"]
        env:
          SLACK_BOT_TOKEN: "your-slack-bot-token"
    ```
    Place this file in the same directory as your agent script or in a parent directory. The `agents-mcp` library will automatically discover it. You can also specify a custom path to the config file.

2.  **Create a `RunnerContext`:**

    The `RunnerContext` object holds the MCP settings. You can create it with or without specifying the config file path. If no path is provided, it will search for `mcp_agent.config.yaml`.

    ```python
    from agents_mcp import RunnerContext

    # Automatic discovery
    context = RunnerContext()

    # Custom config path
    context = RunnerContext(mcp_config_path="/path/to/your/config.yaml")
    ```

3.  **Create an `Agent`:**

    Use the `agents_mcp.Agent` class to create your agent. Specify the following:

    *   `name`: A name for your agent.
    *   `instructions`: Instructions for the agent, describing its role and capabilities.
    *   `tools`: (Optional) A list of local tools (functions decorated with `@function_tool`) that the agent can use.
    *   `mcp_servers`: A list of MCP server names (as defined in your `mcp_agent.config.yaml`) that the agent should connect to.

    ```python
    from agents_mcp import Agent
    from agents import function_tool

    # Example local tool
    @function_tool
    def get_current_weather(location: str) -> str:
        """Get the current weather for a location."""
        return f"The weather in {location} is sunny."

    agent = Agent(
        name="MyAgent",
        instructions="You are a helpful assistant with access to MCP tools.",
        tools=[get_current_weather],  # Optional local tools
        mcp_servers=["fetch", "filesystem", "slack"],  # MCP servers to use
    )
    ```

4.  **Run the Agent:**

    Use the `Runner.run` or `Runner.run_streamed` methods to run your agent.

    ```python
    from agents import Runner
    import asyncio

    async def main():
        context = RunnerContext()
        agent = Agent(
            name="MyAgent",
            instructions="You are a helpful assistant.",
            mcp_servers=["fetch", "filesystem"],
        )

        # Run and get the complete result
        result = await Runner.run(
            starting_agent=agent,
            input="What's the weather in Miami?",
            context=context,
        )
        print(result.final_output)

        # Run and stream the result
        result_streamed = Runner.run_streamed(
            agent,
            input="Print the first paragraph of https://openai.github.io/openai-agents-python/",
            context=context
        )

        async for event in result_streamed.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)

    if __name__ == "__main__":
        asyncio.run(main())

    ```

## Example: Combining Local and MCP Tools (`hello_world_mcp.py`)

```python
import asyncio
from agents import Runner, function_tool
from agents_mcp import Agent, RunnerContext

# Local tool
@function_tool
def get_current_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"The weather in {location} is currently sunny and 72 degrees Fahrenheit."

async def main():
    context = RunnerContext()  # Automatically loads MCP config

    agent = Agent(
        name="MCP Assistant",
        instructions="You are a helpful assistant with access to local and MCP tools.",
        tools=[get_current_weather],  # Include the local tool
        mcp_servers=["fetch", "filesystem"],  # Use fetch and filesystem MCP servers
    )

    result = await Runner.run(
        starting_agent=agent,
        input="What's the weather in Miami?",
        context=context,
    )
    print(f"Weather query result: {result.final_output}")

    result = await Runner.run(
        starting_agent=agent,
        input="Print the first paragraph of https://openai.github.io/openai-agents-python/",
        context=context,
    )
    print(f"Website content result: {result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())
```

This example demonstrates how to combine a local tool (`get_current_weather`) with tools from MCP servers (`fetch` and `filesystem`). The agent can seamlessly use both types of tools to fulfill user requests.

## Example: Streaming Responses (`hello_world_mcp_streamed.py`)
The `hello_world_mcp_streamed.py` example is almost identical to `hello_world_mcp.py`, but uses `Runner.run_streamed` instead of `Runner.run`. This allows you to process the agent's response as it's being generated, rather than waiting for the entire response to complete. This is useful for providing a more interactive user experience.

## Example: Slack Integration (`slack.py`)

```python
import asyncio
import time
from agents import Runner
from agents_mcp import Agent, RunnerContext
from openai.types.responses import ResponseTextDeltaEvent

async def main():
    context = RunnerContext()

    agent = Agent(
        name="Slack Agent",
        instructions="""You are an agent with access to the filesystem and Slack.
                        Identify the closest match to a user's request, make tool calls,
                        and return the results.""",
        tools=[],  # No local tools in this example
        mcp_servers=["filesystem", "slack"],  # Use filesystem and slack MCP servers
    )

    # First query
    print("\n\n--- FIRST QUERY ---")
    print("Searching for the last message in the general channel...\n")
    result = Runner.run_streamed(
        agent,
        input="What was the last message in the general channel?",
        context=context,
    )
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)
    
    # Follow-up query
    print("\n\n--- FOLLOW-UP QUERY ---")
    print("Asking for a summary of the returned information...\n")

    result = Runner.run_streamed(
        agent,
        input=f"Summarize {result.final_output} for me and save it as convo.txt in the current directory.",
        context=context,
    )

    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)

    end = time.time()
    print(f"\n\nTotal run time: {end - start:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
```

This example demonstrates a more complex scenario where the agent interacts with Slack through an MCP server. It also shows how to handle multi-turn conversations by using the output of one query as input for a follow-up query.

## Differences in Approaches and Complexity

The examples demonstrate different levels of complexity:

*   **`hello_world_mcp.py` and `hello_world_mcp_streamed.py`:** These are basic examples showing how to create an agent, connect to MCP servers, and use tools.  The streamed version adds the complexity of handling streaming responses.
*   **`slack.py`:** This is a more advanced example that demonstrates a real-world integration with Slack. It also shows how to handle multi-turn conversations.

The main differences are in the complexity of the tasks the agents are designed to perform and whether they use streaming or non-streaming responses. The underlying mechanism for connecting to MCP servers and using their tools remains the same.

## Key Files in `src/agents_mcp/`

*   **`agent.py`:**  Defines the `Agent` class, which extends the base `Agent` class from the OpenAI Agent SDK.  It handles loading MCP tools and cleaning up resources.
*   **`tools.py`:**  Provides utility functions for converting MCP tools to OpenAI Agent SDK tools, including schema sanitization and content conversion.
* **`context.py`:** Defines the `RunnerContext` class, which manages MCP settings and the server registry.
* **`server_registry.py`:** Handles loading and managing MCP server configurations.
* **`aggregator.py`:**  Manages connections to multiple MCP servers.

This guide provides a starting point for creating OpenAI agents with MCP tools. By combining the power of LLMs with the functionality of external systems, you can build sophisticated agents that can perform a wide range of tasks.