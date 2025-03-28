# Firecrawl MCP Guide

This guide provides an overview of the Firecrawl MCP server and its available tools, along with examples for each. Firecrawl is a powerful web scraping and crawling tool that can be integrated into your workflows via the Model Context Protocol (MCP).

## Available Tools

The Firecrawl MCP server (`mcp-server-firecrawl`) provides the following tools:

*   **`firecrawl_scrape`:** Scrape a single webpage with advanced options.
*   **`firecrawl_map`:** Discover URLs from a starting point.
*   **`firecrawl_crawl`:** Crawl multiple pages asynchronously.
*   **`firecrawl_batch_scrape`:** Scrape multiple URLs in batch mode.
*   **`firecrawl_check_batch_status`:** Check the status of a batch scraping job.
*   **`firecrawl_check_crawl_status`:** Check the status of a crawl job.
*   **`firecrawl_search`:** Search and retrieve content from web pages.
*   **`firecrawl_extract`:** Extract structured information using LLM.
*   **`firecrawl_deep_research`:** Conduct deep research on a query.
*   **`firecrawl_generate_llmstxt`:** Generate LLMs.txt file for a given URL.

## `firecrawl_scrape`

This tool scrapes a single webpage and provides various options for content extraction.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "The URL to scrape"
    },
    "formats": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "markdown",
          "html",
          "rawHtml",
          "screenshot",
          "links",
          "screenshot@fullPage",
          "extract"
        ]
      },
      "description": "Content formats to extract (default: ['markdown'])"
    },
    "onlyMainContent": {
      "type": "boolean",
      "description": "Extract only the main content"
    },
    "includeTags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "HTML tags to specifically include"
    },
    "excludeTags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "HTML tags to exclude"
    },
    "waitFor": {
      "type": "number",
      "description": "Time to wait for dynamic content (ms)"
    },
    "timeout": {
      "type": "number",
      "description": "Maximum time to wait for the page to load (ms)"
    },
    "actions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": [
              "wait",
              "click",
              "screenshot",
              "write",
              "press",
              "scroll",
              "scrape",
              "executeJavascript"
            ]
          },
          "selector": {
            "type": "string",
            "description": "CSS selector for the target element"
          },
          "milliseconds": { "type": "number" },
          "text": { "type": "string" },
          "key": { "type": "string" },
          "direction": { "type": "string", "enum": ["up", "down"] },
          "script": { "type": "string" },
          "fullPage": { "type": "boolean" }
        },
        "required": ["type"]
      }
    },
    "extract": {
      "type": "object",
      "properties": {
        "schema": { "type": "object", "additionalProperties": true },
        "systemPrompt": { "type": "string" },
        "prompt": { "type": "string" }
      },
      "required": ["schema", "systemPrompt", "prompt"]
    },
    "mobile": { "type": "boolean" },
    "skipTlsVerification": { "type": "boolean" },
    "removeBase64Images": { "type": "boolean" },
    "location": {
      "type": "object",
      "properties": {
        "country": { "type": "string" },
        "languages": { "type": "array", "items": { "type": "string" } }
      }
    }
  },
  "required": ["url"]
}
```

**Example (Basic Markdown):**

```json
{
  "url": "https://example.com",
  "formats": ["markdown"]
}
```

**Example (Exclude Tags):**

```json
{
  "url": "https://example.com",
  "formats": ["html"],
  "excludeTags": ["footer", "header", "nav"]
}
```

**Example (Extract with Schema):**

```json
{
  "url": "https://example.com",
  "formats": ["extract"],
  "extract": {
    "schema": {
      "type": "object",
      "properties": {
        "title": { "type": "string" },
        "author": { "type": "string" }
      },
      "required": ["title"]
    },
    "systemPrompt": "You are extracting structured data from a webpage.",
    "prompt": "Extract the title and author."
  }
}
```

## `firecrawl_map`

Discovers URLs from a starting point, using either sitemap.xml or HTML link discovery.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "Starting URL for URL discovery"
    },
    "search": {
      "type": "string",
      "description": "Optional search term to filter URLs"
    },
    "ignoreSitemap": {
      "type": "boolean",
      "description": "Skip sitemap.xml discovery"
    },
    "sitemapOnly": {
      "type": "boolean",
      "description": "Only use sitemap.xml for discovery"
    },
    "includeSubdomains": {
      "type": "boolean",
      "description": "Include URLs from subdomains"
    },
    "limit": {
      "type": "number",
      "description": "Maximum number of URLs to return"
    }
  },
  "required": [
    "url"
  ]
}
```

**Example (Basic Sitemap Discovery):**

```json
{
  "url": "https://example.com"
}
```

**Example (HTML Link Discovery, Limit 10):**

```json
{
  "url": "https://example.com",
  "ignoreSitemap": true,
  "limit": 10
}
```

## `firecrawl_crawl`
Starts an asynchronous crawl of multiple pages.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "url": { "type": "string" },
    "excludePaths": { "type": "array", "items": { "type": "string" } },
    "includePaths": { "type": "array", "items": { "type": "string" } },
    "maxDepth": { "type": "number" },
    "ignoreSitemap": { "type": "boolean" },
    "limit": { "type": "number" },
    "allowBackwardLinks": { "type": "boolean" },
    "allowExternalLinks": { "type": "boolean" },
    "webhook": { "type": "string" },
    "deduplicateSimilarURLs": { "type": "boolean" },
    "ignoreQueryParameters": { "type": "boolean" },
    "scrapeOptions": {
      "type": "object",
      "properties": {
        "formats": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "markdown",
              "html",
              "rawHtml",
              "screenshot",
              "links",
              "screenshot@fullPage",
              "extract"
            ]
          }
        },
        "onlyMainContent": { "type": "boolean" },
        "includeTags": { "type": "array", "items": { "type": "string" } },
        "excludeTags": { "type": "array", "items": { "type": "string" } },
        "waitFor": { "type": "number" }
      }
    }
  },
  "required": ["url"]
}
```

**Example (Crawl with Max Depth 2):**

```json
{
  "url": "https://example.com",
  "maxDepth": 2
}
```

## `firecrawl_batch_scrape`

Scrapes multiple URLs in batch mode.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "urls": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "options": {
      "type": "object",
      "properties": {
        "formats": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "markdown",
              "html",
              "rawHtml",
              "screenshot",
              "links",
              "screenshot@fullPage",
              "extract"
            ]
          }
        },
        "onlyMainContent": { "type": "boolean" },
        "includeTags": { "type": "array", "items": { "type": "string" } },
        "excludeTags": { "type": "array", "items": { "type": "string" } },
        "waitFor": { "type": "number" }
      }
    }
  },
  "required": ["urls"]
}
```

**Example (Batch Scrape Two URLs):**

```json
{
  "urls": ["https://example.com/page1", "https://example.com/page2"],
  "options": {
    "formats": ["markdown"]
  }
}
```

## `firecrawl_extract`
Extracts structured information from web pages using an LLM.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "urls": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "prompt": {
      "type": "string"
    },
    "systemPrompt": {
      "type": "string"
    },
    "schema": {
      "type": "object",
      "properties": {},
      "additionalProperties": true
    },
    "allowExternalLinks": {
      "type": "boolean"
    },
    "enableWebSearch": {
      "type": "boolean"
    },
    "includeSubdomains": {
      "type": "boolean"
    }
  },
  "required": [
    "urls"
  ]
}
```

**Example:**
```json
{
"urls": ["https://www.example.com/blog-post"],
"prompt": "Extract the title, author, and publication date of the blog post.",
"systemPrompt": "You are an AI assistant extracting structured data from web pages.",
"schema": {
  "type": "object",
  "properties": {
    "title": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "publication_date": {
      "type": "string",
      "format": "date"
    }
  },
  "required": [
    "title",
    "author",
    "publication_date"
  ]
}
}
```

**Example (Rental Listings):**

```json
{
  "urls": ["https://www.daft.ie/property-for-rent/clontarf-dublin?numBeds_from=2&numBeds_to=2&rentalPrice_to=2500"],
  "prompt": "Extract rental listing details, including title, price, location, number of bedrooms and bathrooms, lease duration, concise description summary, and listing URL.",
  "systemPrompt": "You are extracting structured data from rental listings.",
  "schema": {
    "type": "object",
    "properties": {
      "listings": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "title": {
              "type": "string"
            },
            "price": {
              "type": "string"
            },
            "location": {
              "type": "string"
            },
            "bedrooms": {
              "type": "integer"
            },
            "bathrooms": {
              "type": "integer"
            },
            "lease_duration": {
              "type": "string"
            },
            "description": {
              "type": "string"
            },
            "url": {
              "type": "string"
            }
          },
          "required": [
            "title",
            "price",
            "location",
            "bedrooms",
            "bathrooms",
            "lease_duration",
            "description",
            "url"
          ]
        }
      }
    },
    "required": [
      "listings"
    ]
  }
}
```

## `firecrawl_check_batch_status`

Checks the status of a batch scraping job.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Batch job ID to check"
    }
  },
  "required": [
    "id"
  ]
}
```

**Example:**

```json
{
  "id": "your-batch-job-id"
}
```

## `firecrawl_check_crawl_status`

Checks the status of a crawl job.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Crawl job ID to check"
    }
  },
  "required": [
    "id"
  ]
}
```

**Example:**

```json
{
  "id": "your-crawl-job-id"
}
```

## `firecrawl_search`
Searches and retrieves content from web pages with optional scraping.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query string"
    },
    "limit": {
      "type": "number",
      "description": "Maximum number of results to return (default: 5)"
    },
    "lang": {
      "type": "string",
      "description": "Language code for search results (default: en)"
    },
    "country": {
      "type": "string",
      "description": "Country code for search results (default: us)"
    },
    "tbs": {
      "type": "string",
      "description": "Time-based search filter"
    },
    "filter": {
      "type": "string",
      "description": "Search filter"
    },
    "location": {
      "type": "object",
      "properties": {
        "country": {
          "type": "string",
          "description": "Country code for geolocation"
        },
        "languages": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Language codes for content"
        }
      },
      "description": "Location settings for search"
    },
    "scrapeOptions": {
      "type": "object",
      "properties": {
        "formats": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "markdown",
              "html",
              "rawHtml"
            ]
          },
          "description": "Content formats to extract from search results"
        },
        "onlyMainContent": {
          "type": "boolean",
          "description": "Extract only the main content from results"
        },
        "waitFor": {
          "type": "number",
          "description": "Time in milliseconds to wait for dynamic content"
        }
      },
      "description": "Options for scraping search results"
    }
  },
  "required": [
    "query"
  ]
}
```
**Example:**
```json
{
    "query": "best pizza in New York",
    "limit": 3,
    "scrapeOptions": {
        "formats": ["markdown"],
        "onlyMainContent": true
    }
}
```

## `firecrawl_deep_research`
Conduct deep research on a query using web crawling, search, and AI analysis.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "The query to research"
    },
    "maxDepth": {
      "type": "number",
      "description": "Maximum depth of research iterations (1-10)"
    },
    "timeLimit": {
      "type": "number",
      "description": "Time limit in seconds (30-300)"
    },
    "maxUrls": {
      "type": "number",
      "description": "Maximum number of URLs to analyze (1-1000)"
    }
  },
  "required": [
    "query"
  ]
}
```
**Example:**
```json
{
    "query": "impact of climate change on coastal cities",
    "maxDepth": 3,
    "timeLimit": 120
}
```

## `firecrawl_generate_llmstxt`

Generates a standardized LLMs.txt file for a given URL.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "The URL to generate LLMs.txt from"
    },
    "maxUrls": {
      "type": "number",
      "description": "Maximum number of URLs to process (1-100, default: 10)"
    },
    "showFullText": {
      "type": "boolean",
      "description": "Whether to show the full LLMs-full.txt in the response"
    }
  },
  "required": [
    "url"
  ]
}
```

**Example:**

```json
{
  "url": "https://example.com",
  "maxUrls": 20
}