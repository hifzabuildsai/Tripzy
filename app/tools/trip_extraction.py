from agents import function_tool

from app.models.trip import TripRequest


@function_tool
def extract_trip_request(
    origin: str | None = None,
    destination: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    start_date_text: str | None = None,
    end_date_text: str | None = None,
    duration_days: int | None = None,
    travelers: int | None = None,
    budget: float | None = None,
    currency: str | None = None,
    interests: list[str] | None = None,
    travel_style: str | None = None,
) -> str:
    """
    Extract travel information explicitly provided by the user.

    Date rules:

    - start_date and end_date are only for fully resolved ISO
      dates in YYYY-MM-DD format.

    - If the user gives a calendar date without enough
      information to determine the year, store the original
      expression in start_date_text or end_date_text instead.

    - Never invent a year.

    Example:

        "September 10"

    becomes:

        start_date_text="September 10"

    NOT:

        start_date="2026-09-10"

    Example:

        "September 10, 2027"

    becomes:

        start_date="2027-09-10"
    """

    trip = TripRequest(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        start_date_text=start_date_text,
        end_date_text=end_date_text,
        duration_days=duration_days,
        travelers=travelers,
        budget=budget,
        currency=currency or "USD",
        interests=interests or [],
        travel_style=travel_style,
    )

    return trip.model_dump_json(
        exclude_none=True,
        exclude_defaults=True,
    )