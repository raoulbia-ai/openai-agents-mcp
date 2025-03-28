## OpenAI + MCP Integration Guide for Firecrawl and Custom Agents

This guide provides a comprehensive reference for integrating OpenAI function-calling agents with custom MCP (Model Context Protocol) servers, using Firecrawl as a practical case study. It outlines the minimal changes required to make MCP tool schemas compliant with OpenAI’s JSON Schema standards, demonstrates how to debug schema mismatches, and provides working examples for Python agent prompts that invoke MCP tools successfully. The guide is structured to help you not only fix Firecrawl-specific issues but also generalize the approach for adapting any custom MCP server to work with OpenAI agents, enabling tool calls, structured data extraction, and advanced agent orchestration.
---

## 🔧 How to Enable `mcp_debug.log` File for MCP Schema Debugging

To inspect what schemas your MCP server sends to OpenAI:

### Step 1: Modify `index.js`
Add this utility at the top of your file:

```js
import fs from 'fs';
const debugLog = (msg) => {
    fs.appendFileSync('mcp_debug.log', `[${new Date().toISOString()}] ${msg}\n`);
};
```

### Step 2: Log the tool schemas
Replace your existing ListToolsRequestSchema handler with:

```js
server.setRequestHandler(ListToolsRequestSchema, async () => {
    const sanitizedTools = TOOLS.map(tool => ({
        ...tool,
        inputSchema: removeUnsupportedJsonSchemaKeywords(tool.inputSchema),
    }));

    debugLog("\uD83D\uDE80 Sending sanitized tool schemas to agent:");
    sanitizedTools.forEach((tool, i) => {
        debugLog(`Tool ${i + 1}: ${tool.name}`);
        debugLog(JSON.stringify(tool.inputSchema, null, 2));
    });

    return { tools: sanitizedTools };
});
```

### Step 3: Run your MCP server
```bash
npm run start
```
This will create and write logs to `mcp_debug.log` in your project root.

---

## 🔧 Minimal Custom Changes to Firecrawl `index.js` for OpenAI Compatibility

These changes make your MCP server schema OpenAI-compatible:

### 1. **Strip unsupported JSON Schema keywords**
Patch `removeUnsupportedJsonSchemaKeywords()`:

```js
function removeUnsupportedJsonSchemaKeywords(schema) {
    if (Array.isArray(schema)) {
        return schema.map(removeUnsupportedJsonSchemaKeywords);
    }
    if (schema && typeof schema === 'object') {
        const cleaned = {};
        for (const key in schema) {
            const value = schema[key];
            if (["anyOf", "allOf", "not"].includes(key)) continue;

            if (key === 'oneOf') {
                const fallback = Array.isArray(value) && value.length > 0 ? value[0] : null;
                if (fallback && fallback.type) {
                    return removeUnsupportedJsonSchemaKeywords(fallback);
                }
                continue;
            }

            cleaned[key] = removeUnsupportedJsonSchemaKeywords(value);
        }

        if (!cleaned.type && cleaned.properties) {
            cleaned.type = 'object';
        }

        return cleaned;
    }
    return schema;
}
```

### 2. **Add `additionalProperties` and `properties` where required**
Ensure all objects have:
```js
properties: {},
additionalProperties: true,
```
especially in:
- `firecrawl_scrape.inputSchema.properties.extract.schema`
- `firecrawl_extract.inputSchema.properties.schema`

---

### 🛠 Optional Bash Patch Script

Create a patcher script like `patch-index.sh`:
```bash
#!/bin/bash
sed -i.bak 's/oneOf:/type: "object"/g' dist/index.js
sed -i.bak 's/"schema": {/"schema": {"type": "object", "properties": {}, "additionalProperties": true,/g' dist/index.js
```
Then:
```bash
npm run build && bash patch-index.sh
```

---

## ⚙️ Custom Changes to Python `firecrawl_example.py`

To make your Python OpenAI agent work with MCP:

### 1. Set `OPENAI_API_KEY`
In your `.env` or explicitly:
```python
import os
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai.api_key  # for trace export
```

### 2. Create a complete and valid tool call prompt
Example:
```python
agent = Agent(
    name="Firecrawl Demo",
    instructions="""
    Use the firecrawl_scrape tool with the following parameters:
    - url: The provided URL
    - formats: ["markdown", "extract"]
    - onlyMainContent: true
    - extract:
        schema:
          type: object
          properties:
            title:
              type: string
            author:
              type: string
          required: ["title"]
          additionalProperties: false
        prompt: "Extract the blog title and author."
        systemPrompt: "You are extracting structured data from HTML."
    """,
    mcp_servers=["mcp-server-firecrawl"]
)
```

### 3. General Approach for Adapting Prompts to Other MCP Servers
To make a valid tool call prompt for **any** MCP tool:

1. Run your MCP server with schema logging enabled (`mcp_debug.log`)
2. Look at the tool name and its `inputSchema` definition
3. Copy the required fields (`required`) and supported `properties`
4. Construct a prompt in this format:
   ```
   Use the TOOL_NAME tool with the following parameters:
   - required_param1: value
   - optional_param2: value (if needed)
   ...
   ```
5. Make sure to match:
   - Enum values (e.g. formats)
   - Nested objects with required subfields
   - Data types (e.g. strings, booleans, objects)

This lets the LLM produce a valid function call for any tool it sees.

---

### 4. Add Timeout and Diagnostics
```python
result = await asyncio.wait_for(Runner.run(...), timeout=30)
```
Log result:
```python
print(json.dumps(result.__dict__, indent=2, default=str))
```

## ➕ Optional Enhancements for Agent-MCP Workflows

### 1. CLI Toggle for Extract Mode
Implement a command-line flag in your Python script to switch between "markdown-only" or "markdown + extract" mode. This can be done using argparse:
```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--extract', action='store_true')
args = parser.parse_args()
```

Use `args.extract` to toggle the `formats` and `extract` block dynamically.

---

### 2. Auto-Discovery of Tool Schemas from MCP
Once `mcp_debug.log` is enabled, parse it to extract schema definitions and generate prompt templates:
- Load JSON schemas
- Identify `required` fields and enums
- Generate a prompt scaffold the LLM can fill in

This can be automated with a Python script that builds `Agent(...instructions=...)` dynamically.

---

### 3. Exporting Structured Output
After a successful tool call:
- Extract relevant data from `result.final_output`
- Optionally save structured response to a file:
```python
with open("output.json", "w") as f:
    json.dump(result.__dict__, f, indent=2, default=str)
```
- You can further parse the `extract` content if JSON is embedded in Markdown.

---

These additional sections offer ways to operationalize the MCP + Agent integration for production use or internal automation workflows.

