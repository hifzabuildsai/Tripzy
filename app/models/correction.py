from pydantic import BaseModel, Field


class TripCorrection(BaseModel):
    """Only the changes explicitly requested for an existing trip."""

    origin: str | None = None
    destination: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    start_date_text: str | None = None
    end_date_text: str | None = None
    duration_days: int | None = None
    travelers: int | None = None
    budget: float | None = None
    currency: str | None = None
    travel_style: str | None = None

    interests_add: list[str] = Field(default_factory=list)
    interests_remove: list[str] = Field(default_factory=list)
    interests_replace: list[str] | None = None
