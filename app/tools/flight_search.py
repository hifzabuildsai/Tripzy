from agents import function_tool

from app.logging_config import logger
from app.tools.search_client import search


@function_tool
def search_flight_information(
    origin: str,
    destination: str,
    departure_date: str,
) -> str:
    """
    Search the web for flight information for a route and date.

    This is a research tool, not a booking or live-availability
    provider.

    Results may contain indicative fares, airlines, routes,
    schedules, or booking pages, but Tripzy must not represent
    them as confirmed live availability.
    """

    query = (
        f"flights from {origin} to {destination} "
        f"on {departure_date} airlines fares schedules"
    )

    response = search(
        query=query,
        search_depth="advanced",
        max_results=5,
    )

    results = response.get(
        "results",
        []
    )

    logger.debug(
        "travel_search_completed",
        extra={
            "stage": "flight_research",
            "result_count": len(results),
        },
    )

    if not results:
        return (
            "No flight research results were found."
        )

    formatted_results = []

    for result in results:

        title = result.get(
            "title",
            "Untitled result",
        )

        url = result.get(
            "url",
            "",
        )

        content = result.get(
            "content",
            "",
        )

        formatted_results.append(
            (
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Content: {content}"
            )
        )

    return "\n\n---\n\n".join(
        formatted_results
    )
