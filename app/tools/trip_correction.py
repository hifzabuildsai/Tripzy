from agents import function_tool

from app.models.correction import TripCorrection


@function_tool
def extract_trip_correction(
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
    travel_style: str | None = None,
    interests_add: list[str] | None = None,
    interests_remove: list[str] | None = None,
    interests_replace: list[str] | None = None,
) -> str:
    """Extract only explicit edits to an already planned trip.

    Interest operations preserve intent: ``interests_add`` and
    ``interests_remove`` update the existing list, while
    ``interests_replace`` is used only when the traveler explicitly asks to
    replace the whole list.
    """

    correction = TripCorrection(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        start_date_text=start_date_text,
        end_date_text=end_date_text,
        duration_days=duration_days,
        travelers=travelers,
        budget=budget,
        currency=currency,
        travel_style=travel_style,
        interests_add=interests_add or [],
        interests_remove=interests_remove or [],
        interests_replace=interests_replace,
    )

    return correction.model_dump_json(
        exclude_none=True,
        exclude_defaults=True,
    )
