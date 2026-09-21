from agents import function_tool

from app.models.trip import TripRequest


@function_tool
def extract_trip_request(
    origin: str | None = None,
    destination: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    duration_days: int | None = None,
    travelers: int | None = None,
    budget: float | None = None,
    currency: str | None = None,
    interests: list[str] | None = None,
    travel_style: str | None = None,
) -> str:
    """
    Extract travel information provided by the user into
    structured TripRequest-compatible data.

    Only fields actually provided by the user should be populated.
    """

    trip = TripRequest(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
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