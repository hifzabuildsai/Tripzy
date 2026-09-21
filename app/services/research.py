from agents import Runner

from app.agents.destination_researcher import (
    destination_researcher,
)
from app.models.research import DestinationResearch


class ResearchService:
    """
    Runs destination research and returns validated structured
    application data.
    """

    async def research_destination(
        self,
        destination: str,
    ) -> DestinationResearch:

        prompt = f"""
Research this travel destination:

{destination}

Use your available travel research tool.

Return structured destination research containing:

- destination
- attractions
- neighborhoods
- transportation
- practical_tips
- local_information
- sources

Do not create an itinerary.

Do not invent facts or source URLs.

The destination field must represent:

{destination}
"""

        result = await Runner.run(
            destination_researcher,
            prompt,
        )

        output = result.final_output

        if isinstance(
            output,
            DestinationResearch,
        ):
            return output

        return DestinationResearch.model_validate(
            output
        )