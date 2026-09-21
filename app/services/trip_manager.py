from typing import Any

from app.models.state import TripState


class TripManager:
    """
    Owns and manages the current Tripzy planning state.

    The TripManager is deliberately deterministic.
    LLMs extract information, but this class decides whether
    the trip is complete and what happens next.
    """

    REQUIRED_FIELDS = [
        "origin",
        "destination",
        "start_date",
        "end_date_or_duration",
        "travelers",
        "budget",
    ]

    def __init__(self):
        self.state = TripState()

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------

    def get_state(self) -> TripState:
        return self.state

    # ---------------------------------------------------------
    # REQUEST DATA
    # ---------------------------------------------------------

    def update_request_fields(self, **fields: Any) -> None:
        """
        Update only valid TripRequest fields.
        """

        allowed_fields = {
            "origin",
            "destination",
            "start_date",
            "end_date",
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

        current_data = self.state.request.model_dump()

        current_data.update(valid_fields)

        self.state.request = type(
            self.state.request
        )(**current_data)

    # ---------------------------------------------------------
    # COMPLETENESS
    # ---------------------------------------------------------

    def get_missing_information(self) -> list[str]:
        """
        Return the required information that is still missing.
        """

        request = self.state.request

        missing = []

        if not request.origin:
            missing.append("origin")

        if not request.destination:
            missing.append("destination")

        if not request.start_date:
            missing.append("start_date")

        if not request.end_date and not request.duration_days:
            missing.append("end_date_or_duration")

        if not request.travelers:
            missing.append("travelers")

        if request.budget is None:
            missing.append("budget")

        return missing

    def is_complete(self) -> bool:
        """
        Determine whether the minimum trip requirements
        have been collected.
        """

        return len(self.get_missing_information()) == 0

    # ---------------------------------------------------------
    # QUESTIONS
    # ---------------------------------------------------------

    def get_next_question(self) -> str | None:
        """
        Return the next question required to complete the trip.
        """

        missing = self.get_missing_information()

        if not missing:
            return None

        questions = {
            "origin": "Where are you travelling from?",

            "destination": (
                "Where would you like to travel to?"
            ),

            "start_date": (
                "When are you planning to travel?"
            ),

            "end_date_or_duration": (
                "How long will you be travelling?"
            ),

            "travelers": (
                "How many people are travelling?"
            ),

            "budget": (
                "What's your approximate travel budget?"
            ),
        }

        return questions[missing[0]]

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def set_status(self, status: str) -> None:
        self.state.status = status

    def get_status(self) -> str:
        return self.state.status

    # ---------------------------------------------------------
    # RESEARCH
    # ---------------------------------------------------------

    def set_destination_research(
        self,
        research: str,
    ) -> None:
        """
        Store destination research in TripState.
        """

        self.state.destination_research = research
        self.state.status = "destination_researched"

    def get_destination_research(self) -> str | None:
        return self.state.destination_research

    # ---------------------------------------------------------
    # PROGRESS
    # ---------------------------------------------------------

    def get_progress(self) -> dict:
        """
        Return a simple snapshot of the planning progress.
        """

        return {
            "complete": self.is_complete(),
            "missing": self.get_missing_information(),
            "status": self.state.status,
            "request": self.state.request.model_dump(),
            "has_destination_research": (
                self.state.destination_research is not None
            ),
        }