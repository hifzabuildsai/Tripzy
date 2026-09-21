from agents import Runner

from app.agents.destination_researcher import (
    destination_researcher,
)


class ResearchService:
    """
    Handles destination research for a completed trip.

    This service is responsible for calling the Destination
    Researcher and returning its final research output.
    """

    async def research_destination(
        self,
        destination: str,
    ) -> str:
        """
        Research a destination using the Destination Researcher.
        """

        prompt = f"""
Research the destination:

{destination}

Use your available travel research tools.

Find useful, current information for a traveler, including:

- major attractions
- important neighborhoods
- transportation
- practical travel considerations
- useful local information

Keep the research concise and useful.

Do not invent facts.

Return a structured research summary suitable for another
travel-planning agent to consume.
"""

        result = await Runner.run(
            destination_researcher,
            prompt,
        )

        return result.final_output