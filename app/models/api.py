from pydantic import BaseModel, Field

from app.config import (
    DEFAULT_MAX_MESSAGE_CHARACTERS,
    get_positive_int,
)
from app.models.state import TripState


MAX_MESSAGE_CHARACTERS = get_positive_int(
    "MAX_MESSAGE_CHARACTERS",
    DEFAULT_MAX_MESSAGE_CHARACTERS,
)


class CreateTripResponse(BaseModel):
    """
    Response returned when Tripzy creates a new
    planning session.
    """

    trip_id: str
    status: str


class TripMessageRequest(BaseModel):
    """
    One user message sent to an existing Tripzy
    planning session.
    """

    message: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_CHARACTERS,
    )


class TripMessageResponse(BaseModel):
    """
    Response returned after Tripzy processes one
    conversation message.
    """

    trip_id: str
    response: str
    status: str
    missing_information: list[str] = Field(
        default_factory=list,
    )


class TripStateResponse(BaseModel):
    """
    API representation of the current Tripzy
    application state.
    """

    trip_id: str
    state: TripState
    missing_information: list[str] = Field(
        default_factory=list,
    )
    clarification: str | None = None
