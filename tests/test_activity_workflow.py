from app.models.activity import (
    ActivityOption,
    ActivityResearch,
)
from app.models.state import TripState
from app.services.conversation import ConversationService
from app.services.trip_manager import TripManager


def build_activity_research() -> ActivityResearch:
    """
    Create deterministic activity research for tests.

    No Gemini or Tavily calls are made.
    """

    return ActivityResearch(
        destination="Istanbul",
        options=[
            ActivityOption(
                name="Hagia Sophia",
                destination="Istanbul",
                category="historical site",
                neighborhood="Sultanahmet",
                description=(
                    "Historic landmark in Istanbul."
                ),
                estimated_duration="1-2 hours",
            ),
            ActivityOption(
                name="Kadikoy Market",
                destination="Istanbul",
                category="food experience",
                neighborhood="Kadikoy",
                description=(
                    "Market and food experience."
                ),
            ),
        ],
        notes=[
            (
                "Test research only. No live availability "
                "is implied."
            )
        ],
    )


def test_trip_state_activity_options_default_empty():
    """
    A new TripState should begin without activity options.
    """

    state = TripState()

    assert state.activity_options == []


def test_activity_research_schema():
    """
    ActivityResearch should preserve typed structured
    activity data.
    """

    research = build_activity_research()

    assert research.destination == "Istanbul"
    assert len(research.options) == 2

    first_activity = research.options[0]

    assert isinstance(
        first_activity,
        ActivityOption,
    )

    assert first_activity.name == "Hagia Sophia"

    assert (
        first_activity.category
        == "historical site"
    )

    assert (
        first_activity.neighborhood
        == "Sultanahmet"
    )


def test_trip_manager_stores_activity_research():
    """
    TripManager should copy validated activity options into
    application-owned TripState.
    """

    manager = TripManager()

    research = build_activity_research()

    manager.set_activity_research(
        research
    )

    options = (
        manager.get_activity_options()
    )

    assert len(options) == 2

    assert (
        options[0].name
        == "Hagia Sophia"
    )

    assert (
        options[1].name
        == "Kadikoy Market"
    )


def test_activity_research_updates_status():
    """
    Storing activity research should advance the deterministic
    workflow status to activities_researched.
    """

    manager = TripManager()

    manager.set_activity_research(
        build_activity_research()
    )

    assert (
        manager.get_status()
        == "activities_researched"
    )


def test_progress_reports_activity_count():
    """
    TripManager progress should expose the number of stored
    activity options.
    """

    manager = TripManager()

    manager.set_activity_research(
        build_activity_research()
    )

    progress = manager.get_progress()

    assert (
        progress["activity_options_count"]
        == 2
    )

    assert (
        progress["status"]
        == "activities_researched"
    )


def test_conversation_service_initializes_activity_service():
    """
    ConversationService should initialize the activity
    research workflow without performing network calls.
    """

    conversation = ConversationService()

    assert (
        conversation.activity_research_service
        is not None
    )

    assert (
        conversation.get_progress()[
            "activity_options_count"
        ]
        == 0
    )