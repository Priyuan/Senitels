import os
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv  # Make sure to add this import

# Load the .env file you just created
load_dotenv()

# Just instantiate the tool. It will find the key automatically.
tavily_tool = TavilySearchResults(max_results=5)

def search_web(query: str) -> str:
    """Search the web using Tavily and return formatted results."""
    results = tavily_tool.invoke({"query": query})  # Use .invoke with a dict argument
    if not results:
        return "No search results found."
    formatted = []
    for r in results:
        formatted.append(f"• {r['content']} (Source: {r['url']})")
    return "\n".join(formatted)