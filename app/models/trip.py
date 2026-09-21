from pydantic import BaseModel, Field
from typing import Optional


class TripRequest(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: Optional[int] = None

    travelers: Optional[int] = None

    budget: Optional[float] = None
    currency: Optional[str] = "USD"

    interests: list[str] = Field(default_factory=list)

    travel_style: Optional[str] = None