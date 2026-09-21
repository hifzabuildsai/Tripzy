from pydantic import BaseModel, Field


class ActivitySource(BaseModel):
    """
    Source from which an activity or place was discovered.

    A source does not imply that Tripzy has verified live
    availability, opening hours, tickets, or pricing.
    """

    title: str
    url: str


class ActivityOption(BaseModel):
    """
    Structured activity or place discovered by Tripzy.

    This represents researched destination information,
    not confirmed live booking availability.
    """

    name: str

    destination: str

    category: str | None = None

    neighborhood: str | None = None

    description: str | None = None

    estimated_duration: str | None = None

    price: float | None = None
    currency: str | None = None

    source: ActivitySource | None = None


class ActivityResearch(BaseModel):
    """
    Structured result produced by the Activities Researcher.

    Activities may include attractions, cultural experiences,
    food experiences, neighborhoods, museums, markets,
    sightseeing, or other useful places and experiences.
    """

    destination: str

    options: list[ActivityOption] = Field(
        default_factory=list
    )

    notes: list[str] = Field(
        default_factory=list
    )