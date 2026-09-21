from agents import Runner

from app.agents.activity_researcher import (
    activity_researcher,
)
from app.models.activity import ActivityResearch
from app.models.research import DestinationResearch
from app.models.trip import TripRequest


class ActivityResearchService:
    """
    Runs activity and place research using both the user's trip
    request and Tripzy's existing destination research.

    The service prepares application-owned context for the
    Activities Researcher.

    The agent performs interpretation and research.
    Python decides which state is supplied to it.
    """

    async def research_activities(
        self,
        request: TripRequest,
        destination_research: DestinationResearch,
    ) -> ActivityResearch:

        neighborhoods = [
            neighborhood.name
            for neighborhood
            in destination_research.neighborhoods
        ]

        known_attractions = [
            attraction.name
            for attraction
            in destination_research.attractions
        ]

        interests = list(
            request.interests
        )

        prompt = f"""
Research useful activities, places, attractions, and
experiences for this Tripzy trip.

==================================================
TRIP CONTEXT
==================================================

Destination:
{request.destination}

Traveler interests:
{interests if interests else "No specific interests provided"}

Travelers:
{request.travelers}

Trip duration:
{request.duration_days if request.duration_days else "Not specified"}

==================================================
EXISTING DESTINATION RESEARCH
==================================================

Useful neighborhoods already discovered:

{neighborhoods}

Known attractions already discovered:

{known_attractions}

==================================================
YOUR TASK
==================================================

Use the available activity search tool.

Pass the following context to the search tool:

- destination
- traveler interests
- known neighborhoods
- known attractions

Use the existing destination research to make the search more
targeted rather than starting from zero.

Research useful:

- attractions
- historical places
- museums
- cultural experiences
- food experiences
- markets
- sightseeing
- local experiences
- other relevant activities supported by the search results

Prioritize the traveler's stated interests when they exist.

You may include known attractions when they are genuinely
relevant, but do not simply copy the existing destination
research.

Discover additional useful activities when the evidence
supports them.

==================================================
ACCURACY RULES
==================================================

Only include information supported by the search results.

Do not invent:

- activities
- places
- neighborhoods
- prices
- durations
- opening hours
- ticket availability
- source URLs

If an optional field is unsupported, leave it empty.

Web research does not establish live ticket availability.

Do not claim that an activity will definitely be open or
available on the traveler's future trip dates.

If prices, opening information, or availability cannot be
verified, explain the limitation in the notes field.

==================================================
SCOPE BOUNDARY
==================================================

Do NOT create a day-by-day itinerary.

Do NOT assign activities to specific days.

Do NOT decide the final schedule.

The later Itinerary Planner will consume these structured
activity options and make scheduling decisions.

Return structured data matching the ActivityResearch schema.

The destination field must represent:

{request.destination}
"""

        result = await Runner.run(
            activity_researcher,
            prompt,
        )

        output = result.final_output

        if isinstance(
            output,
            ActivityResearch,
        ):
            return output

        return ActivityResearch.model_validate(
            output
        )