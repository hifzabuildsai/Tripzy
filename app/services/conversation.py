import json

from agents import Runner

from app.agents.trip_planner import trip_planner
from app.services.research import ResearchService
from app.services.trip_manager import TripManager


class ConversationService:
    """
    Main application-level conversation coordinator.

    Responsibilities:

    1. Receive user messages.
    2. Ask Tripzy to extract travel information.
    3. Update TripManager.
    4. Ask missing questions.
    5. Automatically start destination research
       when the trip becomes complete.
    """

    def __init__(self):
        self.trip_manager = TripManager()
        self.research_service = ResearchService()
        self.last_question: str | None = None

    async def process_message(
        self,
        user_message: str,
    ) -> str:

        user_message = user_message.strip()

        if not user_message:
            return self._get_next_question()

        current_state = self.trip_manager.get_state()

        current_request = current_state.request.model_dump()

        missing_information = (
            self.trip_manager.get_missing_information()
        )

        next_missing_field = (
            missing_information[0]
            if missing_information
            else None
        )

        prompt = f"""
You are processing the user's latest answer in an ongoing
travel-planning conversation.

CURRENT TRIP STATE:

{json.dumps(current_request, indent=2)}

CURRENT REQUIRED MISSING INFORMATION:

{json.dumps(missing_information, indent=2)}

THE NEXT FIELD WE ARE TRYING TO COLLECT:

{next_missing_field}

THE QUESTION THAT WAS ASKED:

{self.last_question}

USER'S LATEST MESSAGE:

{user_message}

Interpret the user's answer according to the current question
and the missing field.

For example:

If the missing field is "origin":

User: Karachi

Extract:

{{
    "origin": "Karachi"
}}

If the missing field is "destination":

User: Istanbul

Extract:

{{
    "destination": "Istanbul"
}}

If the missing field is "travelers":

User: Me and my sister

Extract:

{{
    "travelers": 2
}}

If the missing field is "budget":

User: $2000

Extract:

{{
    "budget": 2000,
    "currency": "USD"
}}

Rules:

- Extract only information actually provided.
- Never invent missing information.
- Never change existing information unless the user
  explicitly corrects it.
- Use extract_trip_request when travel information
  is present.
- Do not perform destination research yourself.
- Do not ask the user a question.
"""

        result = await Runner.run(
            trip_planner,
            prompt,
        )

        extracted_data = self._extract_tool_output(result)

        if extracted_data:

            print("\n🧠 EXTRACTED TRIP DATA")
            print(
                json.dumps(
                    extracted_data,
                    indent=2,
                )
            )

            self.trip_manager.update_request_fields(
                **extracted_data
            )

        # -----------------------------------------------------
        # CHECK WHETHER TRIP IS COMPLETE
        # -----------------------------------------------------

        if not self.trip_manager.is_complete():

            next_question = (
                self.trip_manager.get_next_question()
            )

            self.last_question = next_question

            return next_question

        # -----------------------------------------------------
        # TRIP COMPLETE
        # -----------------------------------------------------

        if (
            self.trip_manager.get_status()
            == "collecting"
        ):
            self.trip_manager.set_status(
                "researching_destination"
            )

            destination = (
                self.trip_manager
                .get_state()
                .request
                .destination
            )

            print(
                "\n🔎 STARTING DESTINATION RESEARCH"
            )

            research = (
                await self.research_service
                .research_destination(
                    destination
                )
            )

            self.trip_manager.set_destination_research(
                research
            )

            print(
                "\n✅ DESTINATION RESEARCH COMPLETE"
            )

            return self._build_research_response(
                research
            )

        # -----------------------------------------------------
        # RESEARCH ALREADY EXISTS
        # -----------------------------------------------------

        research = (
            self.trip_manager
            .get_destination_research()
        )

        if research:
            return research

        return (
            "Your trip information is complete."
        )

    # ---------------------------------------------------------
    # TOOL OUTPUT
    # ---------------------------------------------------------

    @staticmethod
    def _extract_tool_output(result) -> dict:

        for item in result.new_items:

            if not hasattr(item, "output"):
                continue

            output = item.output

            if not isinstance(output, str):
                continue

            try:
                data = json.loads(output)

            except json.JSONDecodeError:
                continue

            if isinstance(data, dict):
                return (
                    ConversationService
                    ._filter_trip_fields(data)
                )

        return {}

    @staticmethod
    def _filter_trip_fields(data: dict) -> dict:

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

        return {
            key: value
            for key, value in data.items()
            if key in allowed_fields
            and value is not None
        }

    # ---------------------------------------------------------
    # QUESTIONS
    # ---------------------------------------------------------

    def _get_next_question(self) -> str:

        question = (
            self.trip_manager
            .get_next_question()
        )

        if question:
            self.last_question = question
            return question

        return (
            "Your trip information is complete."
        )

    # ---------------------------------------------------------
    # RESEARCH RESPONSE
    # ---------------------------------------------------------

    @staticmethod
    def _build_research_response(
        research: str,
    ) -> str:

        return (
            "✈️ Your trip details are complete.\n\n"
            "🔎 I researched your destination.\n\n"
            f"{research}\n\n"
            "Next, we'll use this research to build "
            "the rest of your trip plan."
        )

    # ---------------------------------------------------------
    # STATE ACCESS
    # ---------------------------------------------------------

    def get_state(self):
        return self.trip_manager.get_state()

    def get_progress(self):
        return self.trip_manager.get_progress()