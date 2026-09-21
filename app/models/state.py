from typing import Any

from pydantic import BaseModel, Field

from app.models.flight import FlightOption
from app.models.hotel import HotelOption
from app.models.research import DestinationResearch
from app.models.trip import TripRequest


class TripState(BaseModel):
    """
    Central state for a Tripzy planning session.

    TripState is the source of truth for the application.

    Agents can interpret and research information, but the
    application owns and persists the actual state.
    """

    request: TripRequest = Field(
        default_factory=TripRequest
    )

    destination_research: (
        DestinationResearch | None
    ) = None

    flight_options: list[FlightOption] = Field(
        default_factory=list
    )

    hotel_options: list[HotelOption] = Field(
        default_factory=list
    )

    activity_options: list[dict[str, Any]] = Field(
        default_factory=list
    )

    itinerary: str | None = None

    status: str = "collecting"