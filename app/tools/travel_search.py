from tavily import TavilyClient
from agents import function_tool

from app.config import TAVILY_API_KEY


tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


@function_tool
def search_travel_information(destination: str) -> str:
    """
    Search the web for current travel information about a destination.
    """

    response = tavily_client.search(
        query=f"travel information about {destination}",
        search_depth="basic",
        max_results=5,
    )

    results = response.get("results", [])

    print("\n🔎 TAVILY SEARCH EXECUTED")
    print(f"Query: travel information about {destination}")
    print(f"Results returned: {len(results)}\n")

    if not results:
        return f"No useful travel information found for {destination}."

    formatted_results = []

    for result in results:
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        content = result.get("content", "")

        formatted_results.append(
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content: {content}"
        )

    return "\n\n---\n\n".join(formatted_results)