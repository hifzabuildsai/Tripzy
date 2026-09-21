from pydantic import BaseModel, Field


class FlightSource(BaseModel):
    """
    Source from which a flight option was discovered.

    A source does not imply that Tripzy has verified live
    booking availability.
    """

    title: str
    url: str


class FlightOption(BaseModel):
    """
    Structured flight option discovered by Tripzy.

    This represents researched flight information, not
    confirmed live booking availability.
    """

    airline: str | None = None

    origin: str
    destination: str

    departure_time: str | None = None
    arrival_time: str | None = None

    duration: str | None = None

    stops: int | None = None

    price: float | None = None
    currency: str | None = None

    source: FlightSource | None = None


class FlightResearch(BaseModel):
    """
    Structured result produced by the Flight Researcher.

    Multiple flight options may be discovered for the same
    route and departure date.
    """

    origin: str
    destination: str
    departure_date: str

    options: list[FlightOption] = Field(
        default_factory=list
    )

    notes: list[str] = Field(
        default_factory=list
    )