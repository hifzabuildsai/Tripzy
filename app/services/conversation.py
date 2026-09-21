import json
from datetime import date, datetime

from agents import Runner

from app.agents.trip_planner import trip_planner
from app.models.research import DestinationResearch
from app.services.research import ResearchService
from app.services.trip_manager import TripManager


class ConversationService:
    """
    Main application-level conversation coordinator.

    Responsibilities:

    1. Receive user messages.
    2. Ask Tripzy to extract travel information.
    3. Update TripManager.
    4. Resolve date-year follow-ups deterministically.
    5. Ask missing questions.
    6. Automatically start destination research.
    7. Store destination research as structured application data.
    8. Prevent completed workflows from re-running tools.

    Architecture rule:

    LLMs interpret and research.

    Python owns:
    - application state
    - completeness
    - date-year resolution
    - workflow transitions
    - presentation formatting
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

        # -----------------------------------------------------
        # COMPLETED DESTINATION RESEARCH
        # -----------------------------------------------------

        if (
            self.trip_manager.get_status()
            == "destination_researched"
        ):
            return self._handle_post_research_message(
                user_message
            )

        # -----------------------------------------------------
        # CURRENT APPLICATION STATE
        # -----------------------------------------------------

        current_state = self.trip_manager.get_state()

        current_request = (
            current_state.request.model_dump()
        )

        missing_information = (
            self.trip_manager
            .get_missing_information()
        )

        next_missing_field = (
            missing_information[0]
            if missing_information
            else None
        )

        # -----------------------------------------------------
        # MISSING DATE YEAR
        # -----------------------------------------------------

        if (
            next_missing_field
            == "start_date_year"
        ):

            resolved = (
                self._resolve_start_date_year(
                    user_message=user_message,
                )
            )

            if resolved:

                print(
                    "\n📅 RESOLVED TRAVEL DATE"
                )

                print(
                    json.dumps(
                        {
                            "start_date": resolved,
                        },
                        indent=2,
                    )
                )

                self.trip_manager.update_request_fields(
                    start_date=resolved,
                )

                return (
                    await self._continue_workflow()
                )

        # -----------------------------------------------------
        # NORMAL LLM EXTRACTION
        # -----------------------------------------------------

        today = date.today()

        prompt = f"""
You are processing the user's latest answer in an ongoing
travel-planning conversation.

==================================================
CURRENT DATE
==================================================

Today's date is:

{today.isoformat()}

Year: {today.year}
Month: {today.month}
Day: {today.day}

Use the current date only when interpreting genuinely relative
expressions such as:

- today
- tomorrow
- next Friday
- next week

Do NOT use the current year to fill in a year that the user
never provided for a calendar date.

For example:

User:
September 10

Correct:

{{
    "start_date_text": "September 10"
}}

Incorrect:

{{
    "start_date": "{today.year}-09-10"
}}

==================================================
CURRENT TRIP STATE
==================================================

{json.dumps(current_request, indent=2)}

==================================================
CURRENT REQUIRED MISSING INFORMATION
==================================================

{json.dumps(missing_information, indent=2)}

==================================================
NEXT FIELD WE ARE TRYING TO COLLECT
==================================================

{next_missing_field}

==================================================
QUESTION THAT WAS ASKED
==================================================

{self.last_question}

==================================================
USER'S LATEST MESSAGE
==================================================

{user_message}

==================================================
EXTRACTION RULES
==================================================

Interpret the user's answer according to the current question
and missing field.

Use extract_trip_request whenever travel information is
present.

Extract ONLY information actually supplied or safely resolved
from an explicit relative date.

Never invent missing information.

Never overwrite existing information unless the user explicitly
corrects it.

Do not perform destination research yourself.

Do not ask the user a question.

==================================================
FIELD EXAMPLES
==================================================

If the missing field is "origin":

User:
Karachi

Extract:

{{
    "origin": "Karachi"
}}

--------------------------------------------------

If the missing field is "destination":

User:
Istanbul

Extract:

{{
    "destination": "Istanbul"
}}

--------------------------------------------------

If the missing field is "travelers":

User:
Me and my sister

Extract:

{{
    "travelers": 2
}}

--------------------------------------------------

If the missing field is "budget":

User:
$2000

Extract:

{{
    "budget": 2000,
    "currency": "USD"
}}

==================================================
DATE RULES
==================================================

Date correctness is critical.

RULE 1:

If the user explicitly provides a complete date including
the year, normalize it to ISO YYYY-MM-DD.

Example:

User:
September 10, 2027

Extract:

{{
    "start_date": "2027-09-10"
}}

--------------------------------------------------

RULE 2:

If the user provides month and day but NO YEAR, DO NOT invent
or infer the year.

Example:

User:
September 10

Extract:

{{
    "start_date_text": "September 10"
}}

NOT:

{{
    "start_date": "{today.year}-09-10"
}}

--------------------------------------------------

RULE 3:

If the user gives a date without a year together with a
duration, preserve both.

Example:

User:
September 10 for 5 days

Extract:

{{
    "start_date_text": "September 10",
    "duration_days": 5
}}

--------------------------------------------------

RULE 4:

Relative dates may be resolved using today's date.

Today is:

{today.isoformat()}

Example:

User:
tomorrow

You may calculate the correct ISO date relative to today.

--------------------------------------------------

RULE 5:

Never silently convert an ambiguous date into a complete date.

Calendar date without year:

September 10

means:

start_date_text = "September 10"

It does NOT mean:

{today.year}-09-10

and it does NOT automatically mean next year.

==================================================
FINAL RULE
==================================================

Your responsibility is:

USER LANGUAGE
    ↓
INTERPRET CONTEXT
    ↓
EXTRACT EXPLICIT INFORMATION
    ↓
extract_trip_request()

Python application logic decides whether enough information
exists to continue.
"""

        result = await Runner.run(
            trip_planner,
            prompt,
        )

        extracted_data = (
            self._extract_tool_output(
                result
            )
        )

        if extracted_data:

            print(
                "\n🧠 EXTRACTED TRIP DATA"
            )

            print(
                json.dumps(
                    extracted_data,
                    indent=2,
                )
            )

            self.trip_manager.update_request_fields(
                **extracted_data
            )

        return await self._continue_workflow()

    # ---------------------------------------------------------
    # WORKFLOW
    # ---------------------------------------------------------

    async def _continue_workflow(
        self,
    ) -> str:

        if not self.trip_manager.is_complete():

            next_question = (
                self.trip_manager
                .get_next_question()
            )

            self.last_question = next_question

            return next_question

        # -----------------------------------------------------
        # START DESTINATION RESEARCH
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
                "\n📦 STRUCTURED DESTINATION RESEARCH"
            )

            print(
                research.model_dump_json(
                    indent=2
                )
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
            return self._build_research_response(
                research
            )

        return (
            "Your trip information is complete."
        )

    # ---------------------------------------------------------
    # POST-RESEARCH CONVERSATION
    # ---------------------------------------------------------

    def _handle_post_research_message(
        self,
        user_message: str,
    ) -> str:

        normalized = (
            user_message
            .strip()
            .lower()
        )

        gratitude_messages = {
            "thanks",
            "thank you",
            "thanks!",
            "thank you!",
            "thx",
            "ty",
        }

        if normalized in gratitude_messages:

            return (
                "You're welcome! Your destination research "
                "is ready. Next, we can build the rest of "
                "your trip plan."
            )

        return (
            "Your destination research is already complete. "
            "The next Tripzy milestone will use it to build "
            "the rest of your trip plan."
        )

    # ---------------------------------------------------------
    # DATE RESOLUTION
    # ---------------------------------------------------------

    def _resolve_start_date_year(
        self,
        user_message: str,
    ) -> str | None:

        request = (
            self.trip_manager
            .get_state()
            .request
        )

        date_text = (
            request.start_date_text
        )

        if not date_text:
            return None

        year = self._extract_year(
            user_message
        )

        if year is None:
            return None

        month_day = self._parse_month_day(
            date_text
        )

        if month_day is None:
            return None

        month, day = month_day

        try:

            resolved_date = date(
                year,
                month,
                day,
            )

        except ValueError:
            return None

        return resolved_date.isoformat()

    @staticmethod
    def _extract_year(
        user_message: str,
    ) -> int | None:

        words = (
            user_message
            .replace(",", " ")
            .replace(".", " ")
            .split()
        )

        for word in words:

            if (
                len(word) == 4
                and word.isdigit()
            ):

                year = int(word)

                if 1900 <= year <= 2200:
                    return year

        return None

    @staticmethod
    def _parse_month_day(
        date_text: str,
    ) -> tuple[int, int] | None:

        formats = (
            "%B %d",
            "%b %d",
            "%d %B",
            "%d %b",
        )

        cleaned = (
            date_text
            .strip()
            .replace(",", "")
        )

        for date_format in formats:

            try:

                parsed = datetime.strptime(
                    cleaned,
                    date_format,
                )

                return (
                    parsed.month,
                    parsed.day,
                )

            except ValueError:
                continue

        return None

    # ---------------------------------------------------------
    # TOOL OUTPUT
    # ---------------------------------------------------------

    @staticmethod
    def _extract_tool_output(
        result,
    ) -> dict:

        for item in result.new_items:

            if not hasattr(
                item,
                "output",
            ):
                continue

            output = item.output

            if not isinstance(
                output,
                str,
            ):
                continue

            try:

                data = json.loads(
                    output
                )

            except json.JSONDecodeError:
                continue

            if isinstance(
                data,
                dict,
            ):

                return (
                    ConversationService
                    ._filter_trip_fields(
                        data
                    )
                )

        return {}

    @staticmethod
    def _filter_trip_fields(
        data: dict,
    ) -> dict:

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

        return {
            key: value
            for key, value in data.items()
            if key in allowed_fields
            and value is not None
        }

    # ---------------------------------------------------------
    # QUESTIONS
    # ---------------------------------------------------------

    def _get_next_question(
        self,
    ) -> str:

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
    # RESEARCH PRESENTATION
    # ---------------------------------------------------------

    @staticmethod
    def _build_research_response(
        research: DestinationResearch,
    ) -> str:
        """
        Convert structured application data into a readable
        CLI response.

        Important:

        DestinationResearch remains structured inside TripState.
        This method is presentation-only.
        """

        sections = [
            "✈️ Your trip details are complete.",
            "",
            f"# Destination Research: {research.destination}",
        ]

        # -----------------------------------------------------
        # ATTRACTIONS
        # -----------------------------------------------------

        if research.attractions:

            sections.extend(
                [
                    "",
                    "## Major Attractions",
                ]
            )

            for attraction in research.attractions:

                sections.append(
                    (
                        f"- **{attraction.name}:** "
                        f"{attraction.description}"
                    )
                )

        # -----------------------------------------------------
        # NEIGHBORHOODS
        # -----------------------------------------------------

        if research.neighborhoods:

            sections.extend(
                [
                    "",
                    "## Important Neighborhoods",
                ]
            )

            for neighborhood in research.neighborhoods:

                sections.append(
                    (
                        f"- **{neighborhood.name}:** "
                        f"{neighborhood.description}"
                    )
                )

        # -----------------------------------------------------
        # TRANSPORTATION
        # -----------------------------------------------------

        if research.transportation:

            sections.extend(
                [
                    "",
                    "## Transportation",
                ]
            )

            for item in research.transportation:

                sections.append(
                    f"- {item}"
                )

        # -----------------------------------------------------
        # PRACTICAL TIPS
        # -----------------------------------------------------

        if research.practical_tips:

            sections.extend(
                [
                    "",
                    "## Practical Travel Considerations",
                ]
            )

            for item in research.practical_tips:

                sections.append(
                    f"- {item}"
                )

        # -----------------------------------------------------
        # LOCAL INFORMATION
        # -----------------------------------------------------

        if research.local_information:

            sections.extend(
                [
                    "",
                    "## Useful Local Information",
                ]
            )

            for item in research.local_information:

                sections.append(
                    f"- {item}"
                )

        # -----------------------------------------------------
        # SOURCES
        # -----------------------------------------------------

        if research.sources:

            sections.extend(
                [
                    "",
                    "## Sources",
                ]
            )

            for source in research.sources:

                sections.append(
                    f"- {source.title}: {source.url}"
                )

        sections.extend(
            [
                "",
                (
                    "Next, we'll use this structured research "
                    "to build the rest of your trip plan."
                ),
            ]
        )

        return "\n".join(
            sections
        )

    # ---------------------------------------------------------
    # STATE ACCESS
    # ---------------------------------------------------------

    def get_state(self):
        return self.trip_manager.get_state()

    def get_progress(self):
        return self.trip_manager.get_progress()