# Use Case: Automated Customer Support Ticket Handling with Knowledge Base Integration

**Scenario:** A company uses Intercom for customer support and has a Verodat workspace containing a knowledge base (FAQs, product documentation, troubleshooting guides). The goal is to automate the handling of common support tickets, reducing the load on human agents.

**MCP Data Source:** A Verodat workspace with datasets containing:

*   **KnowledgeBaseArticles:**  (Dataset ID: `kb_articles`) - Contains articles with fields like `article_id` (string, key), `title` (string), `content` (string), `product` (string), `keywords` (string array).
*   **ProductInformation:** (Dataset ID: `product_info`) - Contains product details with fields like `product_id` (string, key), `name` (string), `description` (string), `price` (number).
*   **TroubleshootingGuides:** (Dataset ID: `troubleshooting`) - Contains step-by-step guides with fields like `guide_id` (string, key), `problem_description` (string), `steps` (string array), `related_products` (string array).

**Agent Roles:**

1.  **Triage Agent:**
    *   Receives the initial customer support ticket from Intercom.
    *   Analyzes the ticket's subject and content to determine the issue's nature.
    *   Uses guardrails to check for sensitive information (e.g., credit card numbers) and potentially redact it.
    *   Handoffs to the `KnowledgeBaseAgent` if the issue seems resolvable with existing knowledge base articles, or to a `HumanAgent` (not implemented here, but conceptually a handoff point) if the issue is complex or requires human intervention.

2.  **KnowledgeBase Agent:**
    *   Receives the ticket information from the `TriageAgent`.
    *   Extracts keywords and relevant product information from the ticket.
    *   Constructs a query to the Verodat `KnowledgeBaseArticles` dataset using the `execute-ai-query` tool, searching for relevant articles.
    *   If relevant articles are found, summarizes the information and provides it as a potential solution to the customer (via a response or by updating the ticket).
    *   If no relevant articles are found, handoffs to a `TroubleshootingAgent` or `HumanAgent`.

3.  **Troubleshooting Agent:**
    *   Receives the ticket information.
    *   Queries the Verodat `TroubleshootingGuides` dataset using `execute-ai-query`, looking for guides matching the problem description.
    *   If a relevant guide is found, provides the steps to the customer.
    *   If no guide is found, or if the steps don't resolve the issue, handoffs to a `HumanAgent`.

**SDK Benefits:**

*   **Handoffs:** Seamlessly transfer the ticket between agents based on the issue's complexity and the availability of relevant information.
*   **Guardrails:** Ensure data privacy and prevent the system from providing incorrect or harmful information.
*   **Tracing:** Allows monitoring of the entire process, identifying bottlenecks and areas for improvement. The tracing would show which agents were involved, which queries were executed, and the final outcome.
* **Multi-agent workflow:** The problem is broken down into smaller tasks handled by specialized agents.

**Edge Cases:**

*   **Complex Tickets:**  Handoff to a human agent.
*   **Data Privacy:** Guardrails to detect and redact sensitive information.
*   **Ambiguous Queries:** The `KnowledgeBaseAgent` could use multiple queries with different keywords or ask clarifying questions to the customer (if interaction is possible).

This use case demonstrates how the OpenAI Agents SDK, combined with MCP, can create a powerful and efficient automated customer support system.

# Use Case: Automated Rental Listing Retrieval and Emailing

**Scenario:** A user wants to receive daily emails with new rental listings from a specific property website.

**MCP Data Source:** Firecrawl MCP server, providing access to web scraping tools.

**Agent Roles:**

1.  **Listing Retrieval Agent:**
    *   Uses the `firecrawl_scrape` tool from the Firecrawl MCP server to retrieve the HTML content of the specified property website's rental listings page.
    *   Parses the HTML content to extract relevant information about each rental listing (e.g., address, price, number of bedrooms, link to listing).
    *   Formats the extracted information into a user-friendly format (e.g., a list or table).
    *   Passes the formatted listing information to the `Email Agent`.

2.  **Email Agent:**
    *   Receives the formatted listing information from the `Listing Retrieval Agent`.
    *   Uses the `send_email` function (adapted from `examples/email/email-agent.py`) to send an email to the user's Gmail address. The email subject should indicate that it contains rental listings, and the body should contain the formatted listing information.

**SDK Benefits:**

*   **MCP Integration:** Seamlessly integrates with the Firecrawl MCP server to leverage its web scraping capabilities.
*   **Multi-agent workflow:** The task is broken down into two main steps: retrieving listings and sending the email.
*   **Extensibility:** The system can be extended to support multiple property websites, different email providers, or more sophisticated filtering of listings.

**Edge Cases:**

*   **Website Structure Changes:** The `Listing Retrieval Agent` might need to be updated if the target website's HTML structure changes.
*   **Email Sending Failures:** The `Email Agent` should handle potential errors during email sending (e.g., invalid credentials, network issues).
*   **No New Listings:** The agent should handle cases where no new listings are found on the website. It could either send an email indicating no new listings or skip sending the email altogether.

This use case demonstrates how to combine the OpenAI Agents SDK with MCP to automate web scraping and data delivery tasks.
