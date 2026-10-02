from agents import function_tool

from app.logging_config import logger
from app.tools.search_client import search


@function_tool
def search_travel_information(destination: str) -> str:
    """
    Search the web for current travel information about a destination.
    """

    response = search(
        query=f"travel information about {destination}",
        search_depth="basic",
        max_results=5,
    )

    results = response.get("results", [])

    logger.debug(
        "travel_search_completed",
        extra={
            "stage": "destination_research",
            "result_count": len(results),
        },
    )

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
