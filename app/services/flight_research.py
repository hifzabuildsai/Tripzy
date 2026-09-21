from agents import Runner

from app.agents.flight_researcher import (
    flight_researcher,
)
from app.models.flight import FlightResearch


class FlightResearchService:
    """
    Runs flight research for a completed trip request.

    The service returns validated structured flight research.

    Important:

    This currently uses web research, not a live flight
    booking or availability provider.
    """

    async def research_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
    ) -> FlightResearch:

        prompt = f"""
Research flight information for this trip:

Origin:
{origin}

Destination:
{destination}

Departure date:
{departure_date}

Use the available flight search tool.

Return structured flight research containing:

- origin
- destination
- departure_date
- flight options
- research limitations or useful notes

Only include flight details supported by the search results.

Do not invent:

- airlines
- prices
- schedules
- durations
- stops
- source URLs

Do not claim that any researched flight is currently
available or bookable.

The final output must represent this route:

{origin} -> {destination}

Departure date:

{departure_date}
"""

        result = await Runner.run(
            flight_researcher,
            prompt,
        )

        output = result.final_output

        if isinstance(
            output,
            FlightResearch,
        ):
            return output

        return FlightResearch.model_validate(
            output
        )