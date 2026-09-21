from datetime import date, timedelta

from agents import Runner

from app.agents.itinerary_planner import (
    itinerary_planner,
)
from app.models.itinerary import Itinerary
from app.models.state import TripState


class ItineraryPlannerService:
    """
    Builds a structured itinerary from Tripzy's existing
    application-owned state.

    Python owns deterministic trip invariants and validates
    the boundary between researched entities and model-made
    planning decisions.

    The LLM may sequence and organize supplied information,
    but it does not own application truth.
    """

    GENERIC_CATEGORIES = {
        "meal",
        "rest",
        "leisure",
        "transport",
        "transit",
        "accommodation",
        "generic",
        "free time",
    }

    GENERIC_TITLES = {
        "accommodation check-in",
        "accommodation check-out",
        "hotel check-in",
        "hotel check-out",
        "check-in",
        "check-out",
    }

    PROHIBITED_FLIGHT_TITLES = {
        "flight arrival",
        "flight departure",
    }

    async def build_itinerary(
        self,
        state: TripState,
    ) -> Itinerary:

        request = state.request

        if not request.destination:
            raise ValueError(
                "Destination is required to build an itinerary."
            )

        if not request.start_date:
            raise ValueError(
                "Start date is required to build an itinerary."
            )

        if not request.duration_days:
            raise ValueError(
                "Trip duration is required to build an itinerary."
            )

        if not request.travelers:
            raise ValueError(
                "Traveler count is required to build an itinerary."
            )

        if state.destination_research is None:
            raise ValueError(
                "Destination research is required to build "
                "an itinerary."
            )

        if not state.activity_options:
            raise ValueError(
                "Activity research is required to build "
                "an itinerary."
            )

        itinerary_dates = (
            self._build_itinerary_dates(
                start_date=request.start_date,
                duration_days=request.duration_days,
            )
        )

        destination_research = (
            state.destination_research.model_dump()
        )

        flight_options = [
            option.model_dump()
            for option in state.flight_options
        ]

        hotel_options = [
            option.model_dump()
            for option in state.hotel_options
        ]

        activity_options = [
            option.model_dump()
            for option in state.activity_options
        ]

        eligible_activity_names = [
            option.name
            for option in state.activity_options
        ]

        prompt = f"""
Build a structured Tripzy itinerary from the application-owned
trip state below.

Use only supplied information.

Do not perform web research.

==================================================
TRIP REQUEST
==================================================

Origin:
{request.origin}

Destination:
{request.destination}

Start date:
{request.start_date}

Trip duration:
{request.duration_days} days

Travelers:
{request.travelers}

Total trip budget:
{request.budget}

Budget currency:
{request.currency}

Traveler interests:
{request.interests}

Travel style:
{request.travel_style}

==================================================
APPLICATION-CALCULATED ITINERARY DATES
==================================================

{itinerary_dates}

These dates are application truth.

Create exactly {request.duration_days} itinerary days.

Use these dates exactly and in this exact order.

Do not independently calculate trip dates.

The itinerary end_date must be:

{itinerary_dates[-1]}

==================================================
DESTINATION RESEARCH — CONTEXT ONLY
==================================================

{destination_research}

Destination research provides supporting context such as:

- neighborhoods
- transportation
- practical considerations
- local information

A named attraction appearing only in destination research is
NOT automatically eligible to become a scheduled activity.

==================================================
RESEARCHED FLIGHT CANDIDATES — NOT SELECTED
==================================================

{flight_options}

These are research candidates.

The traveler has NOT selected or booked any of these flights.

Therefore:

- do not schedule a candidate flight
- do not use candidate arrival time as trip truth
- do not use candidate departure time as trip truth
- do not say the traveler is flying on a particular airline
- do not infer a return flight
- do not invent a departure time
- do not create airport-transfer blocks based only on these
  candidates

==================================================
RESEARCHED HOTEL CANDIDATES — NOT SELECTED
==================================================

{hotel_options}

These are research candidates.

The traveler has NOT selected or booked any hotel.

Do not choose one for the traveler.

Do not name one as the traveler's accommodation.

Generic accommodation references are allowed.

==================================================
ELIGIBLE SCHEDULED ACTIVITIES
==================================================

{activity_options}

The following are the ONLY researched named visitor
activities that may be scheduled:

{eligible_activity_names}

IMPORTANT:

When scheduling one of these activities, copy its name
EXACTLY as supplied.

Do not:

- rename it
- paraphrase it
- abbreviate it
- correct its spelling
- translate it
- change accents or Unicode characters

For example, if the supplied activity name is:

Kadıköy Market

the itinerary item title must also be exactly:

Kadıköy Market

Do not schedule another named attraction, market, museum,
tour, restaurant, or visitor experience merely because it
appears elsewhere in destination research.

Generic blocks such as meals, rest, free time,
accommodation check-in/check-out, and generic local
transfers are allowed.

==================================================
FIRST AND FINAL DAY
==================================================

There is no explicitly selected flight in the current state.

Therefore:

- arrival time is unknown
- return departure time is unknown

Do not schedule around researched flight candidate times.

Do not create a "Flight Arrival" item.

Do not create a "Flight Departure" item.

Do not create an airport-transfer item solely from candidate
flight research.

Do not describe the final day as a departure day unless
explicit selected travel data supports that claim.

Keep first-day and final-day planning appropriately flexible.

==================================================
PLANNING RULES
==================================================

Prioritize traveler interests.

Group eligible activities geographically when supported by
their neighborhood data.

Do not force every eligible activity into the itinerary.

Avoid unnecessarily overloaded days.

Leave reasonable space for:

- generic meals
- generic transfers
- rest
- free time

Approximate schedule times are planning decisions.

They are not verified venue opening hours.

Do not invent factual travel times.

Do not invent prices.

Do not claim that anything has been booked or reserved.

==================================================
OUTPUT INVARIANTS
==================================================

Destination:

{request.destination}

Start date:

{request.start_date}

End date:

{itinerary_dates[-1]}

Travelers:

{request.travelers}

Required itinerary day count:

{request.duration_days}

Required date sequence:

{itinerary_dates}

Return structured data matching the Itinerary schema.

Use planning_notes for important assumptions and limitations.
"""

        result = await Runner.run(
            itinerary_planner,
            prompt,
        )

        output = result.final_output

        if isinstance(
            output,
            Itinerary,
        ):
            itinerary = output
        else:
            itinerary = (
                Itinerary.model_validate(
                    output
                )
            )

        self._validate_itinerary(
            itinerary=itinerary,
            destination=request.destination,
            start_date=request.start_date,
            travelers=request.travelers,
            expected_dates=itinerary_dates,
            eligible_activity_names=(
                eligible_activity_names
            ),
        )

        return itinerary

    @staticmethod
    def _build_itinerary_dates(
        start_date: str,
        duration_days: int,
    ) -> list[str]:
        """
        Deterministically calculate the calendar date assigned
        to each itinerary day.
        """

        if duration_days <= 0:
            raise ValueError(
                "Trip duration must be greater than zero."
            )

        try:
            first_day = date.fromisoformat(
                start_date
            )

        except ValueError as error:
            raise ValueError(
                "Start date must use ISO YYYY-MM-DD format."
            ) from error

        return [
            (
                first_day
                + timedelta(days=offset)
            ).isoformat()
            for offset in range(
                duration_days
            )
        ]

    @classmethod
    def _validate_itinerary(
        cls,
        itinerary: Itinerary,
        destination: str,
        start_date: str,
        travelers: int,
        expected_dates: list[str],
        eligible_activity_names: list[str],
    ) -> None:
        """
        Fail closed when the model changes application-owned
        itinerary invariants or mutates researched activity
        identities.
        """

        if itinerary.destination != destination:
            raise ValueError(
                "Planner changed the trip destination."
            )

        if itinerary.start_date != start_date:
            raise ValueError(
                "Planner changed the trip start date."
            )

        expected_end_date = expected_dates[-1]

        if itinerary.end_date != expected_end_date:
            raise ValueError(
                "Planner changed the application-calculated "
                "itinerary end date."
            )

        if itinerary.travelers != travelers:
            raise ValueError(
                "Planner changed the traveler count."
            )

        if len(itinerary.days) != len(
            expected_dates
        ):
            raise ValueError(
                "Planner returned an incorrect number "
                "of itinerary days."
            )

        actual_dates = [
            day.date
            for day in itinerary.days
        ]

        if actual_dates != expected_dates:
            raise ValueError(
                "Planner changed the application-calculated "
                "itinerary dates."
            )

        expected_day_numbers = list(
            range(
                1,
                len(expected_dates) + 1,
            )
        )

        actual_day_numbers = [
            day.day_number
            for day in itinerary.days
        ]

        if (
            actual_day_numbers
            != expected_day_numbers
        ):
            raise ValueError(
                "Planner returned an invalid itinerary "
                "day sequence."
            )

        eligible_activity_name_set = set(
            eligible_activity_names
        )

        for day in itinerary.days:
            for item in day.items:

                normalized_title = (
                    item.title
                    .strip()
                    .lower()
                )

                if (
                    normalized_title
                    in cls.PROHIBITED_FLIGHT_TITLES
                ):
                    raise ValueError(
                        "Planner scheduled an unselected "
                        "flight candidate."
                    )

                category = (
                    item.category
                    .strip()
                    .lower()
                    if item.category
                    else None
                )

                if (
                    category in cls.GENERIC_CATEGORIES
                    or normalized_title in cls.GENERIC_TITLES
                ):
                    continue

                if (
                    item.title
                    not in eligible_activity_name_set
                ):
                    raise ValueError(
                        "Planner scheduled or renamed a "
                        "specific activity outside the "
                        "structured activity research "
                        "boundary: "
                        f"{item.title}"
                    )