# **Agents on Rails: Prompting AI Systems That Stay on Track**

When I started experimenting with OpenAI’s Agents SDK and the MCP (Model Context Protocol) extension package from #Lastmile AI, I expected the challenges to be mostly architectural—tool integration, orchestration logic, maybe API quirks. But what stood out instead was something quieter and far more foundational: prompt design. Not just what the agents *do*, but *how* we tell them to do it.

Unlike prompt-tuning for chat interfaces, working with agentic systems shifts the focus. These aren’t one-shot conversations. Each agent gets a fixed instruction block—its "job description"—and that determines how it behaves throughout the system. What you write in that prompt affects tool usage, output formatting, error resilience, and whether the agent plays nicely with others in the orchestration. And quietly making all this possible behind the scenes is MCP, a protocol that lets agents use third-party tools as if they were built-ins.

This article explores practical learnings from a weekend project where I developed a simple multi-agent application. The application scrapes a rental listings website, extracts listings details as per my requirements, and then emails them to me. The system comprised four agents (URL extractor, detail scraper, email preparer, orchestrator), and building it provided valuable insights into multi-agent orchestration, which I'll discuss below. 

---

## Anatomy of an Effective Agent Prompt

Across the three main agent types—extractors, generators, and orchestrators—some patterns emerged.

### 1. Structure Mirrors Role

The `ListingURLsAgent` and `IndividualListingAgent` are both MCP-enabled and rely on a third-party scraper (Firecrawl) via an MCP server. Their prompts are rigid, task-specific, and tool-constrained:

- Use a specific tool via MCP (i used `firecrawl` from #Firecrawl)   
- Follow an exact schema for input/output  
- Avoid any deviation or extra text

This worked because MCP abstracted the scraping logic. The prompt didn’t need to explain how to fetch a page, parse HTML, or sanitize output. Instead, the agent could simply invoke `firecrawl_scrape` with well-structured instructions. MCP served as the integration layer that kept the prompt focused on orchestration logic, not implementation.

The `EmailMetadataAgent`, meanwhile, is a simple output generator. Its prompt is short and declarative—no tool use, no ambiguity. It defines the values outright:

> "Always use `email@example.com as the recipient…"

This contrast highlights that the presence of MCP and tool invocation influences the design of the prompt itself. With tool-enabled agents, prompts appear to work best if they act like clear API clients—concise, precise, and schema-aligned.

### 2. Orchestrators Depend on Reliable Tools

The `OrchestratorAgent` prompt reads like a high-level playbook:

- It defines sequential steps  
- Assigns each subtask to a named agent-tool  
- Specifies behavior: "Use this tool", "Handle errors", "Don’t proceed before the previous step completes"

This orchestration logic only works because the orchestrator trusts that the sub-agents are MCP-connected and tool-capable. MCP provides the contract: if an agent uses `firecrawl_scrape`, the orchestrator can assume it won’t fail due to integration gaps—it either returns expected data or a controlled error. That’s critical when composing multiple agents into a single workflow.

---

## Takeaways for Prompting Agents

From reviewing these prompts, a few lessons emerged that might help others building agentic systems:

**1. Match prompt structure to agent role**  
For MCP-connected extractors: go schema-first, tool-locked, and deterministic.  
For content generators: constrain the format and values tightly.  
For orchestrators: define steps, not just goals—especially when coordinating tools.

**2. Prompt + MCP = Separation of Concerns**  
Thanks to MCP, prompts didn’t have to encode how to scrape or how to email. They could focus purely on what to extract and when to act. This abstraction keeps agents lean and focused.

**3. Tool use must be crystal clear**  
If an agent can call tools, the prompt must say:  
What tool to use  
What parameters to provide  
What structure to expect  
What not to do (e.g., "Do not return extra text")

**4. Orchestration is about logic, not smarts**  
The orchestrator isn’t "intelligent"—it’s a planner. Its prompt must specify control flow. MCP gives it reliable building blocks, but the prompt has to stack them in the right order.

---

## Final Thoughts

The Model Context Protocol didn’t get much attention in the prompts themselves—but it was the silent enabler behind all of them. Because the agents could rely on standardized, plug-and-play tools like Firecrawl (exposed via MCP), the prompts could focus on logic, structure, and behavior, not scraping syntax or API quirks.

In this setup, prompting is less about creativity and more about clarity. You define a contract: "Here’s your role. Here’s your tool. Here’s what I expect." That level of precision is what lets agents behave predictably—even across multi-step workflows.

Agentic AI isn’t just about autonomy. It’s about composition. And when you pair thoughtful prompt design with infrastructure like MCP, you start to see what truly modular, maintainable AI systems can look like.

*P.S. I’ve shared the code and prompts for this project in a linked Gist the comments.*

---

**No doubt agentic generative AI will very rapidly improve its ability to understand and infer user intent, and the need for putting agents on rails through prompt engineering will become less important. But for now, it’s the only way to keep them on track.**
