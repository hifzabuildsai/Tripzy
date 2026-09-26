from pydantic import BaseModel, Field

from app.models.activity import ActivityOption
from app.models.flight import FlightOption
from app.models.hotel import HotelOption
from app.models.itinerary import Itinerary
from app.models.research import DestinationResearch
from app.models.trip import TripRequest


class TripState(BaseModel):
    """
    Central state for a Tripzy planning session.

    TripState is the source of truth for the application.

    Agents can interpret, research, and plan information, but
    the application owns and persists the actual state.
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

    activity_options: list[ActivityOption] = Field(
        default_factory=list
    )

    itinerary: Itinerary | None = None

    # Persisted only while a completed trip is awaiting correction details.
    # It lets a later clarification resume selective replanning without
    # discarding unaffected research.
    revision_pending_artifacts: list[str] = Field(
        default_factory=list
    )

    status: str = "collecting"
