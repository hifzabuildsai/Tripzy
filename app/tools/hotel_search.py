from agents import function_tool
from tavily import TavilyClient

from app.config import TAVILY_API_KEY


@function_tool
def search_hotel_information(
    destination: str,
    check_in_date: str,
    travelers: int,
    check_out_date: str | None = None,
) -> str:
    """
    Search the web for hotel and accommodation information.

    This is a research tool, not a live hotel booking or
    availability provider.

    Results may contain hotel names, neighborhoods, indicative
    prices, ratings, descriptions, or booking pages.

    Tripzy must not represent these results as confirmed live
    room availability or guaranteed prices.
    """

    client = TavilyClient(
        api_key=TAVILY_API_KEY
    )

    date_context = (
        f"check-in {check_in_date}"
    )

    if check_out_date:
        date_context += (
            f" check-out {check_out_date}"
        )

    query = (
        f"hotels in {destination} "
        f"{date_context} "
        f"for {travelers} travelers "
        "hotel prices neighborhoods ratings accommodation"
    )

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
    )

    results = response.get(
        "results",
        []
    )

    print(
        "\n🏨 HOTEL SEARCH EXECUTED"
    )

    print(
        f"Destination: {destination}"
    )

    print(
        f"Check-in: {check_in_date}"
    )

    if check_out_date:
        print(
            f"Check-out: {check_out_date}"
        )

    print(
        f"Travelers: {travelers}"
    )

    print(
        f"Results returned: {len(results)}"
    )

    if not results:
        return (
            "No hotel research results were found."
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