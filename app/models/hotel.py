from pydantic import BaseModel, Field


class HotelSource(BaseModel):
    """
    Source from which a hotel option was discovered.

    A source does not imply that Tripzy has verified live
    room availability or a guaranteed booking price.
    """

    title: str
    url: str


class HotelOption(BaseModel):
    """
    Structured hotel option discovered by Tripzy.

    This represents researched accommodation information,
    not confirmed live booking availability.
    """

    name: str

    destination: str

    neighborhood: str | None = None

    description: str | None = None

    price_per_night: float | None = None
    currency: str | None = None

    rating: float | None = None

    source: HotelSource | None = None


class HotelResearch(BaseModel):
    """
    Structured result produced by the Hotel Researcher.

    Multiple hotel options may be discovered for the same
    destination and trip dates.
    """

    destination: str

    check_in_date: str
    check_out_date: str | None = None

    travelers: int

    budget: float | None = None
    currency: str | None = None

    options: list[HotelOption] = Field(
        default_factory=list
    )

    notes: list[str] = Field(
        default_factory=list
    )