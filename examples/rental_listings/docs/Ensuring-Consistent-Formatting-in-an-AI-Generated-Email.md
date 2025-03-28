# Ensuring Consistent Formatting in an AI-Generated Rental Listings Email

When building an AI-driven rental listing bot, maintaining a consistent output format is crucial for a professional, easy-to-read email. In this scenario, multiple agents (via OpenAI's Agent SDK with MCP coordination and Firecrawl for scraping) gather structured data successfully – but the final **EmailAgent** sometimes produces an inconsistently formatted summary email. Below, we outline best practices and techniques to enforce reliable formatting in that email, including prompt engineering tactics, markdown structuring, using the Agent SDK’s output schema features, and leveraging templates or schemas (Pydantic models, Jinja2) for consistency.

## Prompt Engineering for Consistent Formatting

The first line of defense is **prompt design**. By giving the EmailAgent very explicit instructions on the desired format, you can greatly reduce variability. Large language models are generative and may otherwise change styles between runs ([LangChain 101 — Lesson 3: Output Parser | by Larry Nguyen | Medium](https://medium.com/@larry_nguyen/langchain-101-lesson-3-output-parser-406591b094d7#:~:text=This%20will%20be%20a%20very,machine%20to%20process%20those%20responses)). Clear instructions act as constraints on the model's output format. Consider these prompt engineering strategies:

- **State the required format explicitly:** For example, tell the agent: *“Present the listings as a bullet-pointed markdown list. Do not include any extra commentary or introduction besides the specified format.”* Being direct about wanting a bulleted list is important ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=Here%20are%20some%20core%20principles,to%20remember)). The prompt should literally mention the format (e.g. “bulleted list”) so the model knows *how* to organize the output.
- **Specify the content order and style:** If each rental listing should follow a template (e.g. **Title** – Price – Location – Link), describe this order in the prompt. You might say: *“For each listing, include the title in bold, then the price, location, and a ‘View listing’ link, in that exact order.”* This ensures each bullet uses the same fields in a consistent sequence.
- **Omit unnecessary text:** Instruct the model not to add any unwanted sections. For instance: *“Do not include an introduction or conclusion; just list the properties.”* This prevents the model from adding greetings or summaries that could break your format ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=1%20__ASK__%202%20Provide%20a,list%20to%20organize%20the%20list)). An example from prompt engineering guides is that adding constraints like “no introduction or conclusion, only a bullet list” yields a focused list output ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=1%20__ASK__%202%20Provide%20a,list%20to%20organize%20the%20list)) ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=Copy%20to%20clipboard)).
- **Provide an example or template (few-shot):** If needed, show the model a mini example of the desired output structure. For instance, in the prompt you could include a dummy listing and how it should be formatted. For example: *“Format: `- **Rental Title** – $Price – Location – [View Listing](URL)`”* as a guide. Seeing a template in the instructions can lock in the format. However, keep the example brief and clearly separated (you can put it in quotes or a code block in the system prompt) so the model understands it as a pattern to follow, not part of the content.
- **Use deterministic settings:** When formatting is critical, run the model at a low temperature (e.g. 0 or 0.2). This reduces randomness so the model is less likely to deviate in style. High creativity isn’t needed for just formatting data, so a strict, low-temperature generation will more reliably obey the instructions.

**Prompt Sample:** To illustrate, you might configure the EmailAgent like so:

```python
email_agent = Agent(
    name="EmailAgent",
    model="gpt-4",  # or a suitable model
    model_settings={"temperature": 0},
    instructions=(
        "You are an assistant that creates a summary email of rental listings.\n"
        "Use the data provided to generate a markdown email with the following format:\n\n"
        "1. Start with a brief one-line intro (e.g. 'Here are the latest rental listings:').\n"
        "2. Then list each property as a separate bullet point in markdown.\n"
        "   - Each bullet should include **Title** – Price, Location – and a link in the format [View Listing](URL).\n"
        "   - Use bold for the title, and ensure each bullet follows the exact same pattern.\n"
        "3. Do not add any additional commentary or sections beyond the list.\n"
        "4. End with a short closing line if needed.\n"
    )
)
```

In this prompt, we clearly enumerate the structure (intro line + bullets) and even specify the markdown syntax for the bullet items. Providing such detailed instructions guides the model toward a consistent output. Being *overly explicit* is usually better than being vague – LLMs perform best when they know exactly what you expect in the output format ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=Here%20are%20some%20core%20principles,to%20remember)) ([LangChain 101 — Lesson 3: Output Parser | by Larry Nguyen | Medium](https://medium.com/@larry_nguyen/langchain-101-lesson-3-output-parser-406591b094d7#:~:text=into%20Issue%2C%20Root%20Causes%20and,and%20many%20more%20variants)).

## Structured Markdown Output (Bullet Lists and Sections)

Using **markdown formatting** (or a similar lightweight markup) is a convenient way to ensure a clean structure in text-based emails. Markdown bullet points, in particular, are easy for the model to produce and for humans to read. To enforce reliable ordering and sectioning:

- **Bullet list for each listing:** Treat each rental listing as one bullet item (`- ...`). This naturally separates items. Make sure to consistently use the same bullet symbol (e.g. `-` or `*`) throughout the prompt and example. If the model sometimes switches to numbers or other symbols, explicitly say “use `-` for each bullet”.
- **Consistent item layout:** Within each bullet, format the content in a repeatable way. A common pattern might be: **Title** – Price – Location – [Link](URL). For example:  

  ```markdown
  - **Sunnyvale 2BR Apartment** – $2,200 – Sunnyvale, CA – [View Listing](https://example.com/listing/123)
  ```  

  All bullets should follow this pattern. You can enforce this by describing the pattern in the prompt and even using field names in bold or punctuation as anchors (like the en dash `–` between pieces). Because your input data from Firecrawl is already structured (e.g. you likely have `title`, `price`, `location`, `url`), you want the EmailAgent to just plug those into the template without reordering. In prompt instructions, mention the fields in the order they should appear. This reduces the chance the model introduces variability (like sometimes putting location before price – which it might do if not told otherwise).
- **Section headings or intro:** If you want an introduction or grouping, you can instruct the model to use a heading or line of text before the list. For instance, a level-2 markdown heading (`## New Rental Listings`) or a brief sentence can introduce the list. Keep this consistent as well. For example, always start with something like: *“Hello,\n\nHere are the latest rental listings in your area:”* followed by the bullets. Because the user’s concern is inconsistent formatting, it may be wise to keep the intro and closing very minimal or templated to avoid any model freestyle that could vary run to run.
- **No missing fields:** If some listings might lack a field (say location is not always available), instruct how to handle it (e.g. skip it or write "Location N/A"). This ensures the format of bullets doesn't break when data varies. Since you noted Firecrawl’s data is consistent, this may not be an issue, but it’s good to mention in instructions if applicable (e.g. “If a field is missing, omit that part but keep the bullet format”).

By using markdown bullets and a fixed schema for each item, you harness the model’s strength in following patterns. As one practitioner noted, without formatting instructions an LLM might return a rambling paragraph, but with clear bullet formatting cues, you get a neatly structured list ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=Copy%20to%20clipboard)). The key is to **show the model what the output should look like**. 

For example, here’s how a **well-formatted output** might look, given the above prompt and properly structured data:

```markdown
Hello,

Here are the latest rental listings in your area:

- **Sunnyvale 2BR Apartment** – $2,200 – Sunnyvale, CA – [View Listing](https://example.com/listing/123)
- **Downtown Loft** – $1,800 – Chicago, IL – [View Listing](https://example.com/listing/456)
- **Cozy Studio** – $1,200 – New York, NY – [View Listing](https://example.com/listing/789)

Best regards,  
Rental Listings Bot
```

Every run of the EmailAgent should ideally produce the same structural format as above, only differing in the content values. If you find the model occasionally deviates (e.g. italicizing something or changing the dash style), reinforce the instructions or add an example to correct that. Often, once the model “learns” the format from your prompt, it will adhere to it strictly, especially with a low-temperature setting.

## Constraining Output with the OpenAI Agent SDK

Beyond prompt wording, the OpenAI Agent SDK itself provides features to enforce structured outputs. In particular, when defining your EmailAgent, you can specify an **`output_type`** – a schema (using Pydantic models, dataclasses, etc.) that the agent *must* follow for its final answer. Using `output_type` effectively tells the model: *“Your final answer isn’t free-form text; it should be a JSON/object matching this schema.”* Under the hood, the Agents SDK uses OpenAI’s structured output (function calling / JSON Schema) to get a deterministic format ([Agents - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/#:~:text=Note)). This means the model will format its answer as JSON conforming to the schema, which the SDK then parses into your specified Python object.

For example, you might define a Pydantic model for the email structure:

```python
from pydantic import BaseModel
from typing import List

class ListingItem(BaseModel):
    title: str
    price: str
    location: str
    url: str

class EmailSummary(BaseModel):
    intro: str
    listings: List[ListingItem]
    closing: str
```

Now create the EmailAgent with this `output_type`:

```python
email_agent = Agent(
    name="EmailAgent",
    instructions=(
       "You are an assistant that formats rental listings into an email.\n"
       "Respond with a JSON object containing an intro line, a list of listings, and a closing line, following the schema provided.\n"
       "{schema}"  # the SDK will include the schema of EmailSummary automatically
    ),
    output_type=EmailSummary,
    model="gpt-4"
)
```

When the agent runs, instead of returning a raw string, it will return an `EmailSummary` object. The content might look like (in JSON form internally):

```json
{
  "intro": "Hello,\n\nHere are the latest rental listings:",
  "listings": [
    {
      "title": "Sunnyvale 2BR Apartment",
      "price": "$2,200",
      "location": "Sunnyvale, CA",
      "url": "https://example.com/listing/123"
    },
    ...
  ],
  "closing": "Best regards,\nRental Listings Bot"
}
```

The Agent SDK will **automatically validate and parse this output** against the `EmailSummary` model ([OpenAI Agents SDK Tutorial: Building AI Systems That Take Action | DataCamp](https://www.datacamp.com/tutorial/openai-agents-sdk-tutorial#:~:text=When%20you%20specify%20the%20,JSON%20parsing%20or%20regex%20extraction)). If the model’s response doesn’t match the schema (e.g. a field is missing or the JSON is invalid), the SDK will throw an error or exception instead of silently giving bad output. This is a powerful way to guarantee structure: you’re effectively constraining the model’s output format using a schema. According to the SDK documentation, by default agents produce plain text, but if you supply an `output_type`, the agent uses structured outputs and you get a Python object instead of a string ([Agents - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/#:~:text=By%20default%2C%20agents%20produce%20plain,dataclasses%2C%20lists%2C%20TypedDict%2C%20etc)) ([Agents - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/#:~:text=When%20you%20pass%20an%20,of%20regular%20plain%20text%20responses)).

**How does this help formatting?** Once you have the email content as a structured object (with an intro, a list of listing items, etc.), you can then format it into the final email with absolute consistency. For instance, you could iterate over `EmailSummary.listings` and construct the markdown bullet list in code, or simply join the pieces with a template. Because the data is guaranteed to be structured, the final formatting step can be made 100% reliable (no surprise model deviations). Essentially, you’re shifting the variable part (LLM generation) to produce structured data, and then using deterministic code to produce the markdown text.

In summary, the Agent SDK’s `output_type` mechanism is a great way to **validate or constrain the output**. It “eliminates the need for manual JSON parsing or regex extraction” by giving you well-formed data directly ([OpenAI Agents SDK Tutorial: Building AI Systems That Take Action | DataCamp](https://www.datacamp.com/tutorial/openai-agents-sdk-tutorial#:~:text=When%20you%20specify%20the%20,JSON%20parsing%20or%20regex%20extraction)). While the SDK doesn’t offer a direct toggle for “enforce markdown bullets” (that must come from either the prompt or post-processing), using an output schema ensures you won’t get extra sentences or a weird format – the model can only fill the fields you defined. This addresses the consistency issue at a structural level.

*Note:* If you go this route, adjust your EmailAgent’s instructions to reflect that it should output JSON. The SDK often injects the schema automatically in the prompt (as a system-level instruction), especially if using function calling under the hood, but it’s good to remind the model to not produce any prose outside the JSON. You might say: *“Output only valid JSON conforming to the schema. Do not add any explanatory text.”* The combination of the automated schema and your instruction will keep the model focused. 

Also, if your final step is actually sending an email (via an email-sending tool in the Agent SDK), you can integrate this by having the EmailAgent produce the final formatted string as one of the fields in the schema (e.g. an `email_body` field containing the markdown text). However, often it’s cleaner to produce structured data and then format it as shown next, especially if you want to ensure the model doesn’t accidentally insert the wrong markdown syntax.

## Leveraging Schemas, Templates, and Post-Processing for Reliability

To achieve maximum consistency, you can combine LLM output schemas with traditional templating. Given that Firecrawl already provides **clean structured data**, you have the option to bypass the LLM for the actual formatting step and use a template engine like **Jinja2** or simple Python string formatting. This guarantees that as long as the data is correct, the email format will be exactly as designed on every run (since code/templates won’t “improvise”). Here are a few techniques:

- **Jinja2 or F-string templates:** You can create a template for the email and fill it with the data. For example, using Jinja2:

  ```python
  from jinja2 import Template

  template_str = """Hello,

  Here are the latest rental listings:

  {% for item in listings %}
  - **{{ item.title }}** – {{ item.price }} – {{ item.location }} – [View Listing]({{ item.url }})
  {% endfor %}

  Best regards,  
  Rental Listings Bot
  """
  template = Template(template_str)
  email_body = template.render(listings=scraped_listings)
  ```
  
  In this template, the structure (hello line, bullet format, closing) is hard-coded. The `scraped_listings` would be the list of listings dictionaries returned by Firecrawl or by the structured EmailAgent. The output `email_body` will be a perfectly formatted markdown every time. This approach uses no AI in the formatting step – the LLM is only used earlier to fetch/extract the data. If your goal is purely consistency and the email doesn’t require nuanced wording beyond the data (e.g. just listing facts), this is a very robust solution.

- **LLM + Jinja hybrid:** If you still want the EmailAgent to do some natural language generation (say writing a sentence or picking a short description), you can combine methods. For instance, have the EmailAgent output a JSON with fields like `intro_sentence`, `listing_lines` (maybe the model can concatenate title + price into a line), etc., then insert those into a template for the final email. Or have the model produce each bullet text as an item in a list (structured), then join them with bullet points. This way the model handles content but you handle format assembly.
- **Output schema validation tools:** Apart from the Agent SDK’s built-in support, there are third-party libraries that help enforce output formats. For example, the **Instructor** and **Marvin** libraries use Pydantic models to validate LLM outputs automatically ([Top 5 Open Source Libraries to structure LLM Outputs](https://hub.athina.ai/top-5-open-source-libraries-to-structure-llm-outputs/#:~:text=,integration%20with%20various%20LLM%20providers)). Tools like **Outlines** provide Jinja2-based prompt templates and even regex checks to constrain the generation ([Top 5 Open Source Libraries to structure LLM Outputs](https://hub.athina.ai/top-5-open-source-libraries-to-structure-llm-outputs/#:~:text=Outlines%20is%20a%20Python%20library,and%20offers%20advanced%20prompting%20features)). And OpenAI’s function calling with JSON Schema is another way to get structured output. All these can be applied to ensure the final step sticks to a format. The common pattern is: *define the schema of the desired output, get the LLM to adhere to it, then render the result using a template or code.* This two-step approach (generation -> rendering) is very reliable for templated outputs.
- **Guardrails and format checkers:** In multi-agent or production setups, you can also include a post-processing check. Libraries like **Guardrails AI** or custom validators can inspect the EmailAgent’s string output to see if it matches the expected pattern (for example, using regex to verify each line starts with "- **" and contains the fields). If not, you could programmatically prompt the agent to fix the format or simply reject and regenerate. The OpenAI Agent SDK’s concept of an output “guardrail” is more about safety filtering, but it hints at ensuring outputs are *“aligned with the intended purpose”* ([Open AI Agents SDK : Unlocking the Future of OpenAI's Game-Changing Agents SDK Update Part-1 - DEV Community](https://dev.to/sreeni5018/open-ai-agents-sdk-unlocking-the-future-of-openais-game-changing-agents-sdk-update-part-1-eai#:~:text=The%20introduction%20of%20Guardrails%20in,aligned%20with%20the%20intended%20purpose)) – in your case, the intended purpose includes a specific format. A lightweight way to implement this: after generation, count the bullets or check for markdown syntax; if something is off, you can supply a corrective prompt like *“The format was slightly incorrect. Please format the email exactly as specified with bullet points for each listing.”* This extra step may not be needed if your initial prompt and schema are strong, but it's an option for extra reliability.

Finally, it’s worth looking at **examples from similar frameworks** for inspiration. In LangChain, for instance, developers faced similar issues where an agent’s answer format would vary and break parsing. The solution was to explicitly prompt for a format and use an output parser to enforce it ([LangChain 101 — Lesson 3: Output Parser | by Larry Nguyen | Medium](https://medium.com/@larry_nguyen/langchain-101-lesson-3-output-parser-406591b094d7#:~:text=In%20my%20work%2C%20I%20need,and%20many%20more%20variants)) ([LangChain 101 — Lesson 3: Output Parser | by Larry Nguyen | Medium](https://medium.com/@larry_nguyen/langchain-101-lesson-3-output-parser-406591b094d7#:~:text=Technically%2C%20I%20could%20create%20the,Comma%20Separated%20List%20and%20Datetime)). The OpenAI Agents SDK essentially has this built in via `output_type`. Another example is a multi-agent news writer project using the OpenAI Agent SDK, where one agent gathered facts and another (similar to your EmailAgent) compiled an email/newsletter. They solved consistency by giving the writing agent a fixed template in the prompt and using markdown for layout (ensuring no lost formatting during agent hand-offs) – a strategy very much in line with what we discussed. The general theme across these projects is: **constrain the generative model with clear instructions and schemas, and/or hand off the formatting to deterministic processes.**

## Summary: Techniques for Reliable Email Formatting

To wrap up, here is a concise list of techniques to turn consistent structured data into a consistent, readable email using LLM agents:

- **Explicit Format Instructions in Prompt:** Clearly describe the desired output format in the EmailAgent’s prompt. For example, specify that the response *must* be a bullet-point list in markdown, and detail the order of information in each bullet ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=1%20__ASK__%202%20Provide%20a,list%20to%20organize%20the%20list)). The more explicit and concrete the instructions (even providing a mini template), the less room for the model to wander.
- **Markdown Bullet List Structure:** Use markdown bullets to list each rental listing, with each bullet following an identical pattern (e.g. "**Title** – Price – Location – [Link](…)"). This makes the output easy to read and ensures uniformity. Instruct the agent with the exact syntax to use (such as the `-` for bullets and the bold ** for titles) so it reproduces them exactly.
- **Low-Variability Generation:** Run the formatting agent with a low temperature and stable settings. This encourages the model to stick to the prompt instructions and not introduce random stylistic changes. Consistency is the priority for this step, so a deterministic approach is best.
- **Use the Agent SDK’s `output_type` for Schema Enforcement:** Take advantage of OpenAI Agent SDK’s ability to enforce structured outputs via Pydantic models ([Agents - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/#:~:text=By%20default%2C%20agents%20produce%20plain,dataclasses%2C%20lists%2C%20TypedDict%2C%20etc)). Define a schema for the email content (like a list of listing items) and set that as the agent’s `output_type`. The SDK will constrain the model to produce JSON fitting that schema, giving you a reliable structured result that you can convert to the email format you need ([OpenAI Agents SDK Tutorial: Building AI Systems That Take Action | DataCamp](https://www.datacamp.com/tutorial/openai-agents-sdk-tutorial#:~:text=When%20you%20specify%20the%20,JSON%20parsing%20or%20regex%20extraction)).
- **Template the Final Output:** Consider using a template (e.g. Jinja2 or even a simple Python format string) to generate the final email text from structured data. Since your data from Firecrawl is already well-structured, you can loop through it to create the bullet list in a hard-coded format. This removes any uncertainty — the format will be exactly as the template dictates on every run. Even if you let the LLM generate some parts, you can template around those parts to keep the overall layout steady.
- **Validate and Iterate:** If absolute consistency is critical, implement a validation step. After the EmailAgent produces the email, quickly check if it matches the expected pattern (number of bullets equals number of listings, all required sections present, etc.). If something is off, you can prompt the agent again with a stricter instruction or use a fallback method (like the template approach). Over time, refining the prompt based on these checks will lead to an extremely robust solution.

By combining these practices, you ensure that the final summary email is not only **informative** but also **uniformly formatted** every time. The key is to leverage the strengths of both AI and deterministic logic: use the LLM for what it’s good at (language and summarization) while boxing in the format using schemas, examples, and templates. Following these methods, your EmailAgent will consistently turn Firecrawl’s structured data into a polished bullet-list email, run after run. 

**Sources:**

- OpenAI Agents SDK Documentation – *Using output schemas to enforce structured outputs* ([Agents - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/#:~:text=By%20default%2C%20agents%20produce%20plain,dataclasses%2C%20lists%2C%20TypedDict%2C%20etc)) ([Agents - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/agents/#:~:text=Note))  
- DataCamp Tutorial – *Structured outputs with Pydantic in Agents SDK* ([OpenAI Agents SDK Tutorial: Building AI Systems That Take Action | DataCamp](https://www.datacamp.com/tutorial/openai-agents-sdk-tutorial#:~:text=When%20you%20specify%20the%20,JSON%20parsing%20or%20regex%20extraction))  
- CodeSignal Prompt Engineering Guide – *Explicit bullet list instructions example* ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=1%20__ASK__%202%20Provide%20a,list%20to%20organize%20the%20list)) ([Bullets of Clarity: Structuring List Responses in Prompt Engineering | CodeSignal Learn](https://codesignal.com/learn/courses/journey-into-format-control-in-prompt-engineering/lessons/bullets-of-clarity-structuring-list-responses-in-prompt-engineering#:~:text=Copy%20to%20clipboard))  
- Medium (Larry Nguyen) – *On output format variability and using output parsers for consistency* ([LangChain 101 — Lesson 3: Output Parser | by Larry Nguyen | Medium](https://medium.com/@larry_nguyen/langchain-101-lesson-3-output-parser-406591b094d7#:~:text=In%20my%20work%2C%20I%20need,and%20many%20more%20variants)) ([LangChain 101 — Lesson 3: Output Parser | by Larry Nguyen | Medium](https://medium.com/@larry_nguyen/langchain-101-lesson-3-output-parser-406591b094d7#:~:text=Technically%2C%20I%20could%20create%20the,Comma%20Separated%20List%20and%20Datetime))  
- Athina AI Blog – *Tools for structured LLM output (Pydantic models, Jinja templates, etc.)* ([Top 5 Open Source Libraries to structure LLM Outputs](https://hub.athina.ai/top-5-open-source-libraries-to-structure-llm-outputs/#:~:text=,integration%20with%20various%20LLM%20providers))