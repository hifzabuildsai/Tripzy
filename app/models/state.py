from typing import Any

from pydantic import BaseModel, Field

from app.models.trip import TripRequest


class TripState(BaseModel):
    """
    Central state for a Tripzy planning session.

    TripState is the source of truth for the application.
    Agents can reason about information, but the application
    owns and persists the actual state.
    """

    request: TripRequest = Field(
        default_factory=TripRequest
    )

    destination_research: str | None = None

    flight_options: list[dict[str, Any]] = Field(
        default_factory=list
    )

    hotel_options: list[dict[str, Any]] = Field(
        default_factory=list
    )

    activity_options: list[dict[str, Any]] = Field(
        default_factory=list
    )

    itinerary: str | None = None

    status: str = "collecting"