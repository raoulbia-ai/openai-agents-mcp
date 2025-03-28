# Agent Libraries Review: `agents` vs `agents_mcp`

## Overview

This document provides a comprehensive review of the two main agent libraries in the OpenAI Agent SDK:

1. **`agents`**: The core agent library for building AI agents with tool-using capabilities
2. **`agents_mcp`**: An extension library that adds Model Context Protocol (MCP) support to agents

## Core Library: `agents`

### Key Components

- **`Agent`**: The main class for creating AI agents
  - Initialized with a name, instructions, and optional tools
  - Tools are added via constructor parameter: `tools=[tool1, tool2]`
  - Uses the `add_tool()` method in some implementations

- **`FunctionTool`**: Converts Python functions into tools that agents can use
  - Automatically generates schema from function signatures and docstrings
  - Example: `FunctionTool(get_listings)`

- **`Runner`**: Executes agents and manages their lifecycle
  - Used via `Runner.run(agent, input="prompt")` 
  - Returns a result object with the agent's output

### Usage Pattern

```python
from agents import Agent, FunctionTool, Runner

# Create a function tool
def get_data():
    """Get some data."""
    return {"key": "value"}

data_tool = FunctionTool(get_data)

# Create an agent with the tool
agent = Agent(
    name="Example Agent",
    instructions="You are a helpful assistant.",
    tools=[data_tool]
)

# Run the agent
result = await Runner.run(agent, "Use the data tool")
print(result.final_output)
```

## MCP Extension: `agents_mcp`

### Key Components

- **`Agent`**: Extended version of the core Agent class with MCP support
  - Initialized with a name, instructions, and optional MCP servers
  - MCP servers are specified via: `mcp_servers=["server-name"]`
  - Does not have an `add_tool()` method - tools are provided through MCP servers

- **`RunnerContext`**: Provides configuration context for running MCP-enabled agents
  - Initialized with an MCP config path: `RunnerContext(mcp_config_path="path/to/config.yaml")`
  - Passed to the Runner when executing the agent

### Configuration

MCP agents require a YAML configuration file that defines:

1. MCP server connections
2. (Optional) Agent configuration

**Simple Configuration Example:**
```yaml
$schema: "https://raw.githubusercontent.com/lastmile-ai/mcp-agent/main/schema/mcp-agent.config.schema.json"
mcp:
  servers:
    mcp-server-firecrawl:
      command: "node"
      args:
        - "path/to/server/index.js"
      env:
        API_KEY: "your-api-key"
name: "AgentName"
instructions: "You are a helpful assistant."
model: "gpt-4-turbo"
```

### Usage Pattern

```python
from agents_mcp import Agent, RunnerContext
from agents import Runner

# Create a context with the config path
context = RunnerContext(mcp_config_path="path/to/config.yaml")

# Create an agent with MCP server
agent = Agent(
    name="MCP Agent",
    instructions="You are a helpful assistant.",
    mcp_servers=["mcp-server-name"]
)

# Run the agent with the context
result = await Runner.run(
    agent,
    input="Use the MCP tool",
    context=context
)
print(result.final_output)
```

## Key Differences

| Feature | `agents` | `agents_mcp` |
|---------|----------|--------------|
| Tool Definition | Defined programmatically in Python | Defined by MCP servers |
| Tool Addition | Via constructor or `add_tool()` method | Via `mcp_servers` parameter |
| Configuration | Minimal, code-based | YAML configuration file |
| External Services | Limited to what can be implemented in Python | Can connect to any service with an MCP server |
| Execution Context | Not required | Requires `RunnerContext` with config path |

## Integration Challenges

When working with MCP agents, several challenges may arise:

1. **Schema Validation Errors**: MCP tools must have valid JSON schemas. Common errors include:
   - Missing `additionalProperties: false` in nested objects
   - Incorrect property types or required fields

2. **Configuration Complexity**: Complex MCP tool schemas in YAML can be error-prone
   - Solution: Use simpler configurations that let the MCP server define its own schemas

3. **Debugging**: MCP integration adds complexity to the debugging process
   - Solution: Use simplified examples first, then add complexity

## Best Practices

1. **Start Simple**: Begin with the simplest possible MCP configuration
   - Define only the server connection, not the tool schemas
   - Let the MCP server provide its own tool definitions

2. **Use the Right Library**: Choose based on your needs
   - Use `agents` for simple, Python-based tools
   - Use `agents_mcp` when you need to integrate with external services

3. **Testing Strategy**: 
   - Test core functionality with mock tools first
   - Then integrate MCP tools with simplified configurations
   - Finally, test with the full production configuration

## Conclusion

The `agents` and `agents_mcp` libraries provide complementary capabilities for building AI agents. The core `agents` library offers a simple, Python-centric approach to tool definition, while `agents_mcp` extends this with the ability to connect to external services through the Model Context Protocol.

By understanding the differences and integration patterns between these libraries, developers can build more powerful and flexible AI agents that leverage both local functionality and external services.