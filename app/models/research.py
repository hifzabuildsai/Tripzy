from pydantic import BaseModel, Field


class Attraction(BaseModel):
    name: str
    description: str


class Neighborhood(BaseModel):
    name: str
    description: str


class ResearchSource(BaseModel):
    title: str
    url: str


class DestinationResearch(BaseModel):
    """
    Structured destination knowledge produced by Tripzy's
    Destination Researcher.

    This becomes application data that downstream agents can
    consume without parsing Markdown.
    """

    destination: str

    attractions: list[Attraction] = Field(
        default_factory=list
    )

    neighborhoods: list[Neighborhood] = Field(
        default_factory=list
    )

    transportation: list[str] = Field(
        default_factory=list
    )

    practical_tips: list[str] = Field(
        default_factory=list
    )

    local_information: list[str] = Field(
        default_factory=list
    )

    sources: list[ResearchSource] = Field(
        default_factory=list
    )