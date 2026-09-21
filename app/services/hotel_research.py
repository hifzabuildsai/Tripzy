from datetime import date, timedelta

from agents import Runner

from app.agents.hotel_researcher import (
    hotel_researcher,
)
from app.models.hotel import HotelResearch
from app.models.trip import TripRequest


class HotelResearchService:
    """
    Runs hotel research for a completed Tripzy trip request.

    Dates are derived deterministically in Python where
    possible.

    Web research is used for accommodation discovery, not
    confirmed live room availability.
    """

    async def research_hotels(
        self,
        request: TripRequest,
    ) -> HotelResearch:

        check_out_date = (
            self._resolve_check_out_date(
                request
            )
        )

        prompt = f"""
Research accommodation options for this trip.

Destination:
{request.destination}

Check-in date:
{request.start_date}

Check-out date:
{check_out_date or "Not specified"}

Travelers:
{request.travelers}

Total trip budget:
{request.budget}

Budget currency:
{request.currency}

IMPORTANT:

The budget above is the TOTAL TRIP BUDGET.

It is NOT automatically the hotel budget.

Do not divide it into a nightly hotel budget.

Use the available hotel search tool.

Return structured hotel research containing:

- destination
- check_in_date
- check_out_date
- travelers
- total trip budget context
- currency
- supported hotel options
- research limitations or useful notes

Only include hotel details supported by the search results.

Do not invent:

- hotels
- neighborhoods
- prices
- ratings
- source URLs

Do not claim that any room is currently available.

Do not claim that any researched price is a guaranteed
live booking price.
"""

        result = await Runner.run(
            hotel_researcher,
            prompt,
        )

        output = result.final_output

        if isinstance(
            output,
            HotelResearch,
        ):
            return output

        return HotelResearch.model_validate(
            output
        )

    @staticmethod
    def _resolve_check_out_date(
        request: TripRequest,
    ) -> str | None:

        if request.end_date:
            return request.end_date

        if (
            not request.start_date
            or not request.duration_days
        ):
            return None

        try:
            check_in = date.fromisoformat(
                request.start_date
            )

            check_out = (
                check_in
                + timedelta(
                    days=request.duration_days
                )
            )

            return check_out.isoformat()

        except ValueError:
            return None