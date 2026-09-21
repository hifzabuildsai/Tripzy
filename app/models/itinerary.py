from pydantic import BaseModel, Field


class ItineraryItem(BaseModel):
    """
    One scheduled item inside a Tripzy itinerary day.

    Items should be based on existing researched trip data
    whenever applicable.
    """

    title: str

    category: str | None = None

    start_time: str | None = None
    end_time: str | None = None

    neighborhood: str | None = None

    description: str | None = None

    estimated_duration: str | None = None

    estimated_cost: float | None = None
    currency: str | None = None

    notes: list[str] = Field(
        default_factory=list
    )


class ItineraryDay(BaseModel):
    """
    One calendar day in the generated trip itinerary.
    """

    day_number: int

    date: str | None = None

    title: str | None = None

    items: list[ItineraryItem] = Field(
        default_factory=list
    )

    notes: list[str] = Field(
        default_factory=list
    )


class Itinerary(BaseModel):
    """
    Structured itinerary generated from Tripzy's researched
    application state.

    The itinerary is planning output, not a representation of
    confirmed bookings or live availability.
    """

    destination: str

    start_date: str

    end_date: str | None = None

    travelers: int

    days: list[ItineraryDay] = Field(
        default_factory=list
    )

    planning_notes: list[str] = Field(
        default_factory=list
    )