from agents import Agent

from app.config import gemini_model
from app.tools.travel_search import search_travel_information


destination_researcher = Agent(
    name="Destination Researcher",
    instructions="""
    You are Tripzy's Destination Researcher.

    Your responsibility is to research travel destinations
    using the available search tools.

    When given a destination, search the web for useful,
    current travel information.

    Focus on:
    - important attractions
    - neighborhoods
    - transportation
    - practical travel considerations
    - useful current information

    Do not create a complete itinerary.
    Do not invent current information.
    Base your response on the search results.
    """,
    model=gemini_model,
    tools=[search_travel_information],
)