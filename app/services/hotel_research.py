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

    Tripzy MVP semantics:

    duration_days represents the number of calendar trip days,
    including the start date.

    Example:

    start_date = 2027-09-10
    duration_days = 5

    Trip dates:
    2027-09-10
    2027-09-11
    2027-09-12
    2027-09-13
    2027-09-14

    Therefore the derived trip/check-out date is 2027-09-14.

    Explicit end_date always takes precedence.

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

The dates above are application-owned trip dates.

Use them exactly.

Do not reinterpret the trip duration or calculate different
hotel dates.

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
            research = output
        else:
            research = HotelResearch.model_validate(
                output
            )

        self._validate_research_dates(
            research=research,
            request=request,
            expected_check_out_date=(
                check_out_date
            ),
        )

        return research

    @staticmethod
    def _resolve_check_out_date(
        request: TripRequest,
    ) -> str | None:
        """
        Resolve the final calendar date of the trip.

        Explicit end_date takes precedence.

        Otherwise duration_days is interpreted as inclusive
        calendar trip days.

        Example:

        start_date = 2027-09-10
        duration_days = 5

        result = 2027-09-14
        """

        if request.end_date:
            return request.end_date

        if (
            not request.start_date
            or not request.duration_days
        ):
            return None

        if request.duration_days <= 0:
            return None

        try:
            check_in = date.fromisoformat(
                request.start_date
            )

            check_out = (
                check_in
                + timedelta(
                    days=(
                        request.duration_days
                        - 1
                    )
                )
            )

            return check_out.isoformat()

        except ValueError:
            return None

    @staticmethod
    def _validate_research_dates(
        research: HotelResearch,
        request: TripRequest,
        expected_check_out_date: str | None,
    ) -> None:
        """
        Fail closed if the model changes application-owned
        hotel research invariants.
        """

        if (
            request.destination
            and research.destination
            != request.destination
        ):
            raise ValueError(
                "Hotel researcher changed the destination."
            )

        if (
            request.start_date
            and research.check_in_date
            != request.start_date
        ):
            raise ValueError(
                "Hotel researcher changed the check-in date."
            )

        if (
            research.check_out_date
            != expected_check_out_date
        ):
            raise ValueError(
                "Hotel researcher changed the application-"
                "calculated check-out date."
            )

        if (
            request.travelers
            and research.travelers
            != request.travelers
        ):
            raise ValueError(
                "Hotel researcher changed the traveler count."
            )