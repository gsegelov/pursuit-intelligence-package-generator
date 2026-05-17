# tools/search_tools.py
# Tool for searching the web using DuckDuckGo
# Used by ClientResearcher

from agents import function_tool
from ddgs import DDGS

@function_tool
def search_web(query: str) -> str:
    """
    Search the web for current information about a company, organization, or topic.
    Use this to research the RFP-issuing organization's background, recent news,
    strategic priorities, and technology context. Run multiple targeted queries
    for comprehensive coverage — one query per topic area.
    """
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return f"No results found for: {query}"
        # Format each result as a readble block the agent can parse
        return "\n\n".join(
            f"Title: {r['title']}\nURL: {r['href']}\nSummary: {r['body']}"
            for r in results
        )
    except Exception as e:
        return f"Error: Search failed for query '{query}'. Reason: {str(e)}"