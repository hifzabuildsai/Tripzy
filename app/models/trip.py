from typing import Optional

from pydantic import BaseModel, Field


class TripRequest(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None

    # Normalized ISO date when fully known: YYYY-MM-DD
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Used when the user gives month/day but no year.
    start_date_text: Optional[str] = None
    end_date_text: Optional[str] = None

    duration_days: Optional[int] = None

    travelers: Optional[int] = None

    budget: Optional[float] = None
    currency: Optional[str] = "USD"

    interests: list[str] = Field(default_factory=list)

    travel_style: Optional[str] = None