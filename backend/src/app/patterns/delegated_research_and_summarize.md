### Delegated Research and Summarization Workflow

**Objective:** To research a complex topic by first performing a web search through a specialized agent, then extracting key points from the search results using another specialized agent, and finally summarizing these key points using a local LLM.

**Input:**
- `input_query`: The complex research topic.

**Workflow:**

1.  **Perform Web Search:**
    Delegate to `WebSearchAgent` to get raw search results for the `input_query`.
    `{{a2a:invoke:agent_url=http://websearch.agent/a2a:capability=perform_search:query={{input_query}}:output_variable=web_search_results}}`

2.  **Extract Key Points:**
    Delegate to `DataAnalysisAgent` to extract key points from the `web_search_results`.
    `{{a2a:invoke:agent_url=http://dataanalysis.agent/a2a:capability=extract_key_points:data={{web_search_results}}:output_variable=extracted_key_points}}`

3.  **Summarize Key Points:**
    Use the local LLM to summarize the `extracted_key_points`.

    **Prompt to LLM:**
    Based on the following key points, please provide a concise summary of the research topic "{{input_query}}":

    {{extracted_key_points}}
```
