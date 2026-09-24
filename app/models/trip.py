from typing import Optional

from pydantic import BaseModel, Field


class TripRequest(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None

    # Normalized ISO date when fully known: YYYY-MM-DD
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Preserves a partial date when either day or year is missing.
    start_date_text: Optional[str] = None
    end_date_text: Optional[str] = None

    duration_days: Optional[int] = None

    travelers: Optional[int] = None

    budget: Optional[float] = None
    currency: Optional[str] = "USD"

    interests: list[str] = Field(default_factory=list)

    travel_style: Optional[str] = None
