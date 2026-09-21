import json
from datetime import date, datetime

from agents import Runner

from app.agents.trip_planner import trip_planner
from app.models.activity import ActivityResearch
from app.models.flight import FlightResearch
from app.models.hotel import HotelResearch
from app.models.itinerary import Itinerary
from app.models.research import DestinationResearch
from app.models.state import TripState
from app.services.activity_research import ActivityResearchService
from app.services.flight_research import FlightResearchService
from app.services.hotel_research import HotelResearchService
from app.services.itinerary_planning import ItineraryPlannerService
from app.services.research import ResearchService
from app.services.trip_manager import TripManager


class ConversationService:
    """
    Main application-level conversation coordinator.

    LLMs interpret and research.

    Python owns:
    - application state
    - completeness
    - date-year resolution
    - workflow transitions
    - presentation formatting
    """

    def __init__(
        self,
        state: TripState | None = None,
   ):
        self.trip_manager = TripManager(
            state=state,
        )

        self.research_service = ResearchService()

        self.flight_research_service = (
            FlightResearchService()
        )

        self.hotel_research_service = (
            HotelResearchService()
        )

        self.activity_research_service = (
            ActivityResearchService()
        )

        self.itinerary_planner_service = (
            ItineraryPlannerService()
        )

        self.last_question: str | None = (
            self.trip_manager.get_next_question()
            if state is not None
            else None
        )

    async def process_message(
        self,
        user_message: str,
    ) -> str:

        user_message = user_message.strip()

        if not user_message:
            return self._get_next_question()

        if (
            self.trip_manager.get_status()
            == "itinerary_planned"
        ):
            return (
                self._handle_completed_research_message(
                    user_message
                )
            )

        current_state = (
            self.trip_manager.get_state()
        )

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

        if next_missing_field == "start_date_year":

            resolved = self._resolve_start_date_year(
                user_message=user_message,
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

                return await self._continue_workflow()

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

If the user explicitly mentions travel interests, extract them.

Examples of interests include:

- history
- food
- museums
- architecture
- nature
- shopping
- culture
- nightlife
- photography

Do not invent interests that the user did not provide.

Do not perform destination, flight, hotel, or activity research
yourself.

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

--------------------------------------------------

If the user explicitly provides interests:

User:
I'm interested in history and food.

Extract:

{{
    "interests": [
        "history",
        "food"
    ]
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

--------------------------------------------------

RULE 5:

Never silently convert an ambiguous date into a complete date.

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

Python application logic decides what happens next.
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

        request = (
            self.trip_manager
            .get_state()
            .request
        )

        status = (
            self.trip_manager
            .get_status()
        )

        # -----------------------------------------------------
        # DESTINATION RESEARCH
        # -----------------------------------------------------

        if status == "collecting":

            self.trip_manager.set_status(
                "researching_destination"
            )

            print(
                "\n🔎 STARTING DESTINATION RESEARCH"
            )

            destination_research = (
                await self.research_service
                .research_destination(
                    request.destination
                )
            )

            self.trip_manager.set_destination_research(
                destination_research
            )

            print(
                "\n📦 STRUCTURED DESTINATION RESEARCH"
            )

            print(
                destination_research.model_dump_json(
                    indent=2
                )
            )

            print(
                "\n✅ DESTINATION RESEARCH COMPLETE"
            )

            status = (
                self.trip_manager
                .get_status()
            )

        # -----------------------------------------------------
        # FLIGHT RESEARCH
        # -----------------------------------------------------

        if status == "destination_researched":

            self.trip_manager.set_status(
                "researching_flights"
            )

            print(
                "\n✈️ STARTING FLIGHT RESEARCH"
            )

            flight_research = (
                await self.flight_research_service
                .research_flights(
                    origin=request.origin,
                    destination=request.destination,
                    departure_date=request.start_date,
                )
            )

            self.trip_manager.set_flight_research(
                flight_research
            )

            print(
                "\n📦 STRUCTURED FLIGHT RESEARCH"
            )

            print(
                flight_research.model_dump_json(
                    indent=2
                )
            )

            print(
                "\n✅ FLIGHT RESEARCH COMPLETE"
            )

            status = (
                self.trip_manager
                .get_status()
            )

        # -----------------------------------------------------
        # HOTEL RESEARCH
        # -----------------------------------------------------

        if status == "flights_researched":

            self.trip_manager.set_status(
                "researching_hotels"
            )

            print(
                "\n🏨 STARTING HOTEL RESEARCH"
            )

            hotel_research = (
                await self.hotel_research_service
                .research_hotels(
                    request
                )
            )

            self.trip_manager.set_hotel_research(
                hotel_research
            )

            print(
                "\n📦 STRUCTURED HOTEL RESEARCH"
            )

            print(
                hotel_research.model_dump_json(
                    indent=2
                )
            )

            print(
                "\n✅ HOTEL RESEARCH COMPLETE"
            )

            status = (
                self.trip_manager
                .get_status()
            )

        # -----------------------------------------------------
        # ACTIVITY RESEARCH
        # -----------------------------------------------------

        if status == "hotels_researched":

            destination_research = (
                self.trip_manager
                .get_destination_research()
            )

            if destination_research is None:
                return (
                    "Tripzy cannot start activity research "
                    "because destination research is missing."
                )

            self.trip_manager.set_status(
                "researching_activities"
            )

            print(
                "\n🎯 STARTING ACTIVITY RESEARCH"
            )

            activity_research = (
                await self.activity_research_service
                .research_activities(
                    request=request,
                    destination_research=(
                        destination_research
                    ),
                )
            )

            self.trip_manager.set_activity_research(
                activity_research
            )

            print(
                "\n📦 STRUCTURED ACTIVITY RESEARCH"
            )

            print(
                activity_research.model_dump_json(
                    indent=2
                )
            )

            print(
                "\n✅ ACTIVITY RESEARCH COMPLETE"
            )

            status = (
                self.trip_manager
                .get_status()
            )

        # -----------------------------------------------------
        # ITINERARY PLANNING
        # -----------------------------------------------------

        if status == "activities_researched":

            self.trip_manager.set_status(
                "planning_itinerary"
            )

            print(
                "\n🗓️ STARTING ITINERARY PLANNING"
            )

            itinerary = (
                await self.itinerary_planner_service
                .build_itinerary(
                    self.trip_manager.get_state()
                )
            )

            self.trip_manager.set_itinerary(
                itinerary
            )

            print(
                "\n📦 STRUCTURED ITINERARY"
            )

            print(
                itinerary.model_dump_json(
                    indent=2
                )
            )

            print(
                "\n✅ ITINERARY PLANNING COMPLETE"
            )

            return self._build_combined_response(
                destination_research=(
                    self.trip_manager
                    .get_destination_research()
                ),
                flight_research=(
                    self._build_flight_research_from_state()
                ),
                hotel_research=(
                    self._build_hotel_research_from_state()
                ),
                activity_research=(
                    self._build_activity_research_from_state()
                ),
                itinerary=itinerary,
            )

        # -----------------------------------------------------
        # ALREADY COMPLETE
        # -----------------------------------------------------

        if status == "itinerary_planned":

            itinerary = (
                self.trip_manager
                .get_itinerary()
            )

            if itinerary is None:
                return (
                    "Tripzy cannot display the itinerary "
                    "because itinerary state is missing."
                )

            return self._build_combined_response(
                destination_research=(
                    self.trip_manager
                    .get_destination_research()
                ),
                flight_research=(
                    self._build_flight_research_from_state()
                ),
                hotel_research=(
                    self._build_hotel_research_from_state()
                ),
                activity_research=(
                    self._build_activity_research_from_state()
                ),
                itinerary=itinerary,
            )

        return (
            "Your trip information is complete."
        )

    # ---------------------------------------------------------
    # COMPLETED WORKFLOW
    # ---------------------------------------------------------

    def _handle_completed_research_message(
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
                "You're welcome! Your Tripzy research and "
                "structured day-by-day itinerary are ready."
            )

        return (
            "Your trip research and structured itinerary are "
            "already complete."
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

        date_text = request.start_date_text

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
    # DESTINATION PRESENTATION
    # ---------------------------------------------------------

    @staticmethod
    def _build_destination_section(
        research: DestinationResearch,
    ) -> list[str]:

        sections = [
            (
                "# Destination Research: "
                f"{research.destination}"
            ),
        ]

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

        return sections

    # ---------------------------------------------------------
    # FLIGHT PRESENTATION
    # ---------------------------------------------------------

    @staticmethod
    def _build_flight_section(
        research: FlightResearch,
    ) -> list[str]:

        sections = [
            "",
            (
                "# Flight Research: "
                f"{research.origin} → "
                f"{research.destination}"
            ),
            "",
            (
                "Departure date: "
                f"{research.departure_date}"
            ),
        ]

        if not research.options:

            sections.extend(
                [
                    "",
                    (
                        "No sufficiently supported structured "
                        "flight options were found."
                    ),
                ]
            )

        for index, option in enumerate(
            research.options,
            start=1,
        ):

            sections.extend(
                [
                    "",
                    f"## Flight Option {index}",
                ]
            )

            if option.airline:
                sections.append(
                    f"- Airline: {option.airline}"
                )

            sections.append(
                (
                    f"- Route: {option.origin} → "
                    f"{option.destination}"
                )
            )

            if option.departure_time:
                sections.append(
                    (
                        "- Departure: "
                        f"{option.departure_time}"
                    )
                )

            if option.arrival_time:
                sections.append(
                    (
                        "- Arrival: "
                        f"{option.arrival_time}"
                    )
                )

            if option.duration:
                sections.append(
                    (
                        "- Duration: "
                        f"{option.duration}"
                    )
                )

            if option.stops is not None:
                sections.append(
                    f"- Stops: {option.stops}"
                )

            if option.price is not None:

                price = (
                    f"{option.price:,.2f}"
                )

                if option.currency:
                    price = (
                        f"{option.currency} {price}"
                    )

                sections.append(
                    f"- Researched price: {price}"
                )

            if option.source:

                sections.append(
                    (
                        "- Source: "
                        f"{option.source.title} "
                        f"({option.source.url})"
                    )
                )

        if research.notes:

            sections.extend(
                [
                    "",
                    "## Flight Research Notes",
                ]
            )

            for note in research.notes:
                sections.append(
                    f"- {note}"
                )

        sections.extend(
            [
                "",
                (
                    "Flight information above is research data, "
                    "not confirmed live booking availability."
                ),
            ]
        )

        return sections

    # ---------------------------------------------------------
    # HOTEL PRESENTATION
    # ---------------------------------------------------------

    @staticmethod
    def _build_hotel_section(
        research: HotelResearch,
    ) -> list[str]:

        sections = [
            "",
            (
                "# Hotel Research: "
                f"{research.destination}"
            ),
            "",
            (
                "Check-in: "
                f"{research.check_in_date}"
            ),
        ]

        if research.check_out_date:
            sections.append(
                (
                    "Check-out: "
                    f"{research.check_out_date}"
                )
            )

        sections.append(
            (
                "Travelers: "
                f"{research.travelers}"
            )
        )

        if not research.options:

            sections.extend(
                [
                    "",
                    (
                        "No sufficiently supported structured "
                        "hotel options were found."
                    ),
                ]
            )

        for index, option in enumerate(
            research.options,
            start=1,
        ):

            sections.extend(
                [
                    "",
                    f"## Hotel Option {index}",
                    f"- Name: {option.name}",
                ]
            )

            if option.neighborhood:
                sections.append(
                    (
                        "- Neighborhood: "
                        f"{option.neighborhood}"
                    )
                )

            if option.description:
                sections.append(
                    (
                        "- Description: "
                        f"{option.description}"
                    )
                )

            if option.price_per_night is not None:

                price = (
                    f"{option.price_per_night:,.2f}"
                )

                if option.currency:
                    price = (
                        f"{option.currency} {price}"
                    )

                sections.append(
                    (
                        "- Researched price/night: "
                        f"{price}"
                    )
                )

            if option.rating is not None:
                sections.append(
                    (
                        "- Rating: "
                        f"{option.rating}"
                    )
                )

            if option.source:
                sections.append(
                    (
                        "- Source: "
                        f"{option.source.title} "
                        f"({option.source.url})"
                    )
                )

        if research.notes:

            sections.extend(
                [
                    "",
                    "## Hotel Research Notes",
                ]
            )

            for note in research.notes:
                sections.append(
                    f"- {note}"
                )

        sections.extend(
            [
                "",
                (
                    "Hotel information above is research data, "
                    "not confirmed live room availability or "
                    "guaranteed booking pricing."
                ),
            ]
        )

        return sections

    # ---------------------------------------------------------
    # ACTIVITY PRESENTATION
    # ---------------------------------------------------------

    @staticmethod
    def _build_activity_section(
        research: ActivityResearch,
    ) -> list[str]:

        sections = [
            "",
            (
                "# Activities & Places: "
                f"{research.destination}"
            ),
        ]

        if not research.options:

            sections.extend(
                [
                    "",
                    (
                        "No sufficiently supported structured "
                        "activity options were found."
                    ),
                ]
            )

        for index, option in enumerate(
            research.options,
            start=1,
        ):

            sections.extend(
                [
                    "",
                    f"## Activity Option {index}",
                    f"- Name: {option.name}",
                ]
            )

            if option.category:
                sections.append(
                    (
                        "- Category: "
                        f"{option.category}"
                    )
                )

            if option.neighborhood:
                sections.append(
                    (
                        "- Neighborhood: "
                        f"{option.neighborhood}"
                    )
                )

            if option.description:
                sections.append(
                    (
                        "- Description: "
                        f"{option.description}"
                    )
                )

            if option.estimated_duration:
                sections.append(
                    (
                        "- Estimated duration: "
                        f"{option.estimated_duration}"
                    )
                )

            if option.price is not None:

                price = (
                    f"{option.price:,.2f}"
                )

                if option.currency:
                    price = (
                        f"{option.currency} {price}"
                    )

                sections.append(
                    (
                        "- Researched price: "
                        f"{price}"
                    )
                )

            if option.source:
                sections.append(
                    (
                        "- Source: "
                        f"{option.source.title} "
                        f"({option.source.url})"
                    )
                )

        if research.notes:

            sections.extend(
                [
                    "",
                    "## Activity Research Notes",
                ]
            )

            for note in research.notes:
                sections.append(
                    f"- {note}"
                )

        sections.extend(
            [
                "",
                (
                    "Activity information above is research "
                    "data, not confirmed live ticket "
                    "availability, opening status, or "
                    "guaranteed pricing."
                ),
            ]
        )

        return sections

    # ---------------------------------------------------------
    # ITINERARY PRESENTATION
    # ---------------------------------------------------------

    @staticmethod
    def _build_itinerary_section(
        itinerary: Itinerary,
    ) -> list[str]:

        sections = [
            "",
            (
                "# Day-by-Day Itinerary: "
                f"{itinerary.destination}"
            ),
            "",
            (
                "Start date: "
                f"{itinerary.start_date}"
            ),
            (
                "Travelers: "
                f"{itinerary.travelers}"
            ),
        ]

        if itinerary.end_date:
            sections.append(
                (
                    "End date: "
                    f"{itinerary.end_date}"
                )
            )

        for day in itinerary.days:

            sections.extend(
                [
                    "",
                    (
                        f"## Day {day.day_number}"
                        + (
                            f" — {day.date}"
                            if day.date
                            else ""
                        )
                    ),
                ]
            )

            if day.title:
                sections.append(
                    f"**{day.title}**"
                )

            if not day.items:
                sections.append(
                    "- No scheduled items."
                )

            for item in day.items:

                time_parts = [
                    value
                    for value in (
                        item.start_time,
                        item.end_time,
                    )
                    if value
                ]

                if len(time_parts) == 2:
                    time_label = (
                        f"{time_parts[0]}–"
                        f"{time_parts[1]}"
                    )
                elif time_parts:
                    time_label = time_parts[0]
                else:
                    time_label = None

                heading = (
                    f"- **{item.title}**"
                )

                if time_label:
                    heading += (
                        f" ({time_label})"
                    )

                sections.append(
                    heading
                )

                if item.category:
                    sections.append(
                        (
                            "  - Category: "
                            f"{item.category}"
                        )
                    )

                if item.neighborhood:
                    sections.append(
                        (
                            "  - Neighborhood: "
                            f"{item.neighborhood}"
                        )
                    )

                if item.description:
                    sections.append(
                        (
                            "  - "
                            f"{item.description}"
                        )
                    )

                if item.estimated_duration:
                    sections.append(
                        (
                            "  - Estimated duration: "
                            f"{item.estimated_duration}"
                        )
                    )

                if item.estimated_cost is not None:

                    cost = (
                        f"{item.estimated_cost:,.2f}"
                    )

                    if item.currency:
                        cost = (
                            f"{item.currency} {cost}"
                        )

                    sections.append(
                        (
                            "  - Researched cost: "
                            f"{cost}"
                        )
                    )

                for note in item.notes:
                    sections.append(
                        f"  - Note: {note}"
                    )

            for note in day.notes:
                sections.append(
                    f"- Day note: {note}"
                )

        if itinerary.planning_notes:

            sections.extend(
                [
                    "",
                    "## Itinerary Planning Notes",
                ]
            )

            for note in itinerary.planning_notes:
                sections.append(
                    f"- {note}"
                )

        sections.extend(
            [
                "",
                (
                    "This itinerary is a planning recommendation "
                    "based on Tripzy's researched data. It does "
                    "not represent confirmed bookings, live "
                    "availability, or guaranteed opening hours."
                ),
            ]
        )

        return sections

    # ---------------------------------------------------------
    # COMBINED PRESENTATION
    # ---------------------------------------------------------

    def _build_combined_response(
        self,
        destination_research: (
            DestinationResearch | None
        ),
        flight_research: FlightResearch,
        hotel_research: HotelResearch,
        activity_research: ActivityResearch,
        itinerary: Itinerary,
    ) -> str:

        sections = [
            (
                "✈️ Your initial trip research is "
                "complete."
            ),
            "",
        ]

        if destination_research:

            sections.extend(
                self._build_destination_section(
                    destination_research
                )
            )

        sections.extend(
            self._build_flight_section(
                flight_research
            )
        )

        sections.extend(
            self._build_hotel_section(
                hotel_research
            )
        )

        sections.extend(
            self._build_activity_section(
                activity_research
            )
        )

        sections.extend(
            self._build_itinerary_section(
                itinerary
            )
        )

        return "\n".join(
            sections
        )

    # ---------------------------------------------------------
    # REBUILD RESEARCH ENVELOPES FROM STATE
    # ---------------------------------------------------------

    def _build_flight_research_from_state(
        self,
    ) -> FlightResearch:

        request = (
            self.trip_manager
            .get_state()
            .request
        )

        return FlightResearch(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.start_date,
            options=(
                self.trip_manager
                .get_flight_options()
            ),
            notes=[],
        )

    def _build_hotel_research_from_state(
        self,
    ) -> HotelResearch:

        request = (
            self.trip_manager
            .get_state()
            .request
        )

        check_out_date = (
            self.hotel_research_service
            ._resolve_check_out_date(
                request
            )
        )

        return HotelResearch(
            destination=request.destination,
            check_in_date=request.start_date,
            check_out_date=check_out_date,
            travelers=request.travelers,
            budget=request.budget,
            currency=request.currency,
            options=(
                self.trip_manager
                .get_hotel_options()
            ),
            notes=[],
        )

    def _build_activity_research_from_state(
        self,
    ) -> ActivityResearch:

        request = (
            self.trip_manager
            .get_state()
            .request
        )

        return ActivityResearch(
            destination=request.destination,
            options=(
                self.trip_manager
                .get_activity_options()
            ),
            notes=[],
        )

    # ---------------------------------------------------------
    # STATE ACCESS
    # ---------------------------------------------------------

    def get_state(self):
        return self.trip_manager.get_state()

    def get_progress(self):
        return self.trip_manager.get_progress()