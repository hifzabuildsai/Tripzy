from typing import Any

from app.models.activity import (
    ActivityOption,
    ActivityResearch,
)
from app.models.flight import (
    FlightOption,
    FlightResearch,
)
from app.models.hotel import (
    HotelOption,
    HotelResearch,
)
from app.models.itinerary import Itinerary
from app.models.research import DestinationResearch
from app.models.state import TripState
from app.services.date_semantics import (
    get_missing_start_date_field,
)


class TripManager:
    """
    Owns and manages the current Tripzy planning state.

    The TripManager is deterministic.

    Agents interpret, research, and plan information.
    TripManager owns application truth and workflow state.

    TripManager can start with either:
    - a fresh TripState
    - an existing restored TripState
    """

    def __init__(
        self,
        state: TripState | None = None,
    ):
        self.state = (
            state
            if state is not None
            else TripState()
        )

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------

    def get_state(self) -> TripState:
        return self.state

    # ---------------------------------------------------------
    # REQUEST DATA
    # ---------------------------------------------------------

    def update_request_fields(
        self,
        **fields: Any,
    ) -> None:

        allowed_fields = {
            "origin",
            "destination",
            "start_date",
            "end_date",
            "start_date_text",
            "end_date_text",
            "duration_days",
            "travelers",
            "budget",
            "currency",
            "interests",
            "travel_style",
        }

        valid_fields = {
            key: value
            for key, value in fields.items()
            if key in allowed_fields
            and value is not None
        }

        if not valid_fields:
            return

        current_data = (
            self.state.request.model_dump()
        )

        current_data.update(
            valid_fields
        )

        self.state.request = type(
            self.state.request
        )(
            **current_data
        )

    # ---------------------------------------------------------
    # COMPLETENESS
    # ---------------------------------------------------------

    def get_missing_information(
        self,
    ) -> list[str]:

        request = self.state.request

        missing = []

        if not request.origin:
            missing.append(
                "origin"
            )

        if not request.destination:
            missing.append(
                "destination"
            )

        if not request.start_date:
            missing.append(
                get_missing_start_date_field(
                    request.start_date_text
                )
            )

        if (
            not request.end_date
            and not request.duration_days
        ):
            missing.append(
                "end_date_or_duration"
            )

        if not request.travelers:
            missing.append(
                "travelers"
            )

        if request.budget is None:
            missing.append(
                "budget"
            )

        return missing

    def is_complete(
        self,
    ) -> bool:

        return (
            len(
                self.get_missing_information()
            )
            == 0
        )

    # ---------------------------------------------------------
    # QUESTIONS
    # ---------------------------------------------------------

    def get_next_question(
        self,
    ) -> str | None:

        missing = (
            self.get_missing_information()
        )

        if not missing:
            return None

        descriptions = {
            "origin": "where you're travelling from",
            "destination": "where you'd like to go",
            "start_date": "your travel start date (including the year)",
            "start_date_year": "the year for your travel start date",
            "start_date_day": "the day of the month for your travel start date",
            "end_date_or_duration": "your end date or trip duration",
            "travelers": "how many people are travelling",
            "budget": "your approximate total budget and currency",
        }

        return (
            "To plan your trip, please share: "
            + "; ".join(descriptions[field] for field in missing)
            + ". You can answer everything in one message."
        )

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def set_status(
        self,
        status: str,
    ) -> None:

        self.state.status = status

    def get_status(
        self,
    ) -> str:

        return self.state.status

    # ---------------------------------------------------------
    # DESTINATION RESEARCH
    # ---------------------------------------------------------

    def set_destination_research(
        self,
        research: DestinationResearch,
    ) -> None:

        self.state.destination_research = (
            research
        )

        self.state.status = (
            "destination_researched"
        )

    def get_destination_research(
        self,
    ) -> DestinationResearch | None:

        return (
            self.state.destination_research
        )

    # ---------------------------------------------------------
    # FLIGHT RESEARCH
    # ---------------------------------------------------------

    def set_flight_research(
        self,
        research: FlightResearch,
    ) -> None:

        self.state.flight_options = list(
            research.options
        )

        self.state.status = (
            "flights_researched"
        )

    def get_flight_options(
        self,
    ) -> list[FlightOption]:

        return self.state.flight_options

    # ---------------------------------------------------------
    # HOTEL RESEARCH
    # ---------------------------------------------------------

    def set_hotel_research(
        self,
        research: HotelResearch,
    ) -> None:

        self.state.hotel_options = list(
            research.options
        )

        self.state.status = (
            "hotels_researched"
        )

    def get_hotel_options(
        self,
    ) -> list[HotelOption]:

        return self.state.hotel_options

    # ---------------------------------------------------------
    # ACTIVITY RESEARCH
    # ---------------------------------------------------------

    def set_activity_research(
        self,
        research: ActivityResearch,
    ) -> None:
        """
        Store validated activity options in TripState.

        ActivityResearch is the research envelope.
        TripState owns the structured ActivityOption list.
        """

        self.state.activity_options = list(
            research.options
        )

        self.state.status = (
            "activities_researched"
        )

    def get_activity_options(
        self,
    ) -> list[ActivityOption]:

        return self.state.activity_options

    # ---------------------------------------------------------
    # ITINERARY
    # ---------------------------------------------------------

    def set_itinerary(
        self,
        itinerary: Itinerary,
    ) -> None:
        """
        Store the validated structured itinerary.

        The itinerary has already passed planner-service
        invariant validation before reaching this method.
        """

        self.state.itinerary = itinerary

        self.state.status = (
            "itinerary_planned"
        )

    def get_itinerary(
        self,
    ) -> Itinerary | None:

        return self.state.itinerary

    # ---------------------------------------------------------
    # PROGRESS
    # ---------------------------------------------------------

    def get_progress(
        self,
    ) -> dict:

        return {
            "complete": (
                self.is_complete()
            ),

            "missing": (
                self.get_missing_information()
            ),

            "status": (
                self.state.status
            ),

            "request": (
                self.state.request.model_dump()
            ),

            "has_destination_research": (
                self.state.destination_research
                is not None
            ),

            "flight_options_count": (
                len(
                    self.state.flight_options
                )
            ),

            "hotel_options_count": (
                len(
                    self.state.hotel_options
                )
            ),

            "activity_options_count": (
                len(
                    self.state.activity_options
                )
            ),

            "has_itinerary": (
                self.state.itinerary
                is not None
            ),
        }
