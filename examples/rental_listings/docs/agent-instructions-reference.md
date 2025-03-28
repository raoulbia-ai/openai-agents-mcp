# 🤖 Agent Instruction Reference

A living repository of agent instruction templates designed to trigger specific behaviors in agentic apps using MCP + OpenAI.

Each block should include:
- ✅ What it does
- 🔧 The instruction block
- 💡 Notes on what it worked well for / failed at

---

## 🏘️ Rental Listing Aggregator (Daft.ie)

**✅ Goal:**
Scrape an overview page of rental listings, then open each one and extract structured details (title, price, location, description).

**🔧 Instructions:**
```
You are a helpful agent designed to summarize rental listings.

1. Use firecrawl_scrape to scrape the listings overview page at the provided URL.
2. From that page, extract links to individual listings.
3. For each listing URL, use firecrawl_scrape again to extract:
    - title
    - price
    - location
    - number of bedrooms
    - number of bathrooms
    - description
4. Return a simple, readable list of all listings with this information.

Make the summary clear and avoid unnecessary commentary.
```

**💡 Notes:**
- Very effective for single-level drill-down workflows
- Response format was consistent
- May need retry logic for large result sets

---

## 🧪 Early Firecrawl Extract Test (Raw Result + Final Output)

**✅ Goal:**
Test Firecrawl’s ability to scrape and extract markdown + structured fields using `extract.schema`, and observe both final and raw outputs.

**🔧 Instructions:**
```
You are a helpful assistant that provides information about rental listings.

When asked about listings, use the firecrawl_scrape tool with the following parameters:
- url: The provided URL
- formats: ["markdown", "extract"]
- onlyMainContent: true
- extract:
    schema:
      type: object
      properties:
        title:
          type: string
        price:
          type: string
        location:
          type: string
        description:
          type: string
      required: ["title", "price"]
      additionalProperties: false
    prompt: "Extract key information about each rental listing such as title, price, location, and description."
    systemPrompt: "You are extracting structured data from rental listings on a webpage."
```

**💡 Notes:**
- Returned both structured JSON output and markdown summary
- Output was verbose due to `result.raw_output` printing
- Good for schema verification and debugging

