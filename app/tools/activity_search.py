from agents import function_tool
from tavily import TavilyClient

from app.config import TAVILY_API_KEY
from app.logging_config import logger


@function_tool
def search_activity_information(
    destination: str,
    interests: list[str] | None = None,
    neighborhoods: list[str] | None = None,
    known_attractions: list[str] | None = None,
) -> str:
    """
    Search the web for activities, attractions, places, and
    experiences relevant to a Tripzy trip.

    Existing destination knowledge and traveler interests may
    be supplied to make the research more targeted.

    This is a research tool, not a live ticketing,
    availability, or booking provider.
    """

    client = TavilyClient(
        api_key=TAVILY_API_KEY
    )

    interests = interests or []
    neighborhoods = neighborhoods or []
    known_attractions = known_attractions or []

    query_parts = [
        (
            f"best activities attractions places experiences "
            f"in {destination}"
        )
    ]

    if interests:
        query_parts.append(
            "traveler interests: "
            + ", ".join(interests)
        )

    if neighborhoods:
        query_parts.append(
            "useful neighborhoods: "
            + ", ".join(neighborhoods)
        )

    if known_attractions:
        query_parts.append(
            "include relevant information about or alternatives "
            "to these known attractions: "
            + ", ".join(known_attractions)
        )

    query_parts.append(
        (
            "museums cultural experiences food markets "
            "sightseeing local experiences admission prices "
            "opening information"
        )
    )

    query = " | ".join(
        query_parts
    )

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=7,
    )

    results = response.get(
        "results",
        []
    )

    logger.debug(
        "travel_search_completed",
        extra={
            "stage": "activity_research",
            "result_count": len(results),
        },
    )

    if not results:
        return (
            "No activity research results were found."
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
