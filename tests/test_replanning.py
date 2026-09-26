import asyncio

import pytest
from fastapi.testclient import TestClient

import app.api as api_module
from app.models.activity import ActivityOption, ActivityResearch
from app.models.correction import TripCorrection
from app.models.flight import FlightOption, FlightResearch
from app.models.hotel import HotelOption, HotelResearch
from app.models.itinerary import Itinerary, ItineraryDay, ItineraryItem
from app.models.research import Attraction, DestinationResearch
from app.models.state import TripState
from app.models.trip import TripRequest
from app.services.conversation import ConversationService
from app.services.in_memory_trip_repository import InMemoryTripRepository
from app.services.replanning import (
    apply_correction,
    invalidated_artifacts,
)
from app.services.session_registry import SessionRegistry


def completed_state() -> TripState:
    return TripState(
        request=TripRequest(
            origin="Karachi",
            destination="Seoul",
            start_date="2027-09-10",
            duration_days=6,
            travelers=2,
            budget=2500,
            currency="USD",
            interests=["food", "culture", "shopping", "cafés"],
            travel_style="relaxed",
        ),
        destination_research=DestinationResearch(
            destination="Seoul",
            attractions=[Attraction(
                name="National Museum of Korea",
                description="Researched museum.",
            )],
        ),
        flight_options=[FlightOption(
            airline="Research Air",
            origin="Karachi",
            destination="Seoul",
        )],
        hotel_options=[HotelOption(
            name="Research Hotel",
            destination="Seoul",
        )],
        activity_options=[ActivityOption(
            name="National Museum of Korea",
            destination="Seoul",
        )],
        itinerary=Itinerary(
            destination="Seoul",
            start_date="2027-09-10",
            end_date="2027-09-15",
            travelers=2,
            days=[ItineraryDay(
                day_number=1,
                date="2027-09-10",
                items=[ItineraryItem(
                    title="National Museum of Korea",
                )],
            )],
        ),
        status="itinerary_planned",
    )


def install_workflow_spies(
    monkeypatch,
    service: ConversationService,
) -> list[str]:
    calls: list[str] = []

    async def destination(destination: str):
        calls.append("destination_research")
        return DestinationResearch(
            destination=destination,
            attractions=[Attraction(
                name=f"{destination} Museum",
                description="Researched museum.",
            )],
        )

    async def flights(origin: str, destination: str, departure_date: str):
        calls.append("flight_options")
        return FlightResearch(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            options=[FlightOption(
                origin=origin,
                destination=destination,
            )],
        )

    async def hotels(request: TripRequest):
        calls.append("hotel_options")
        return HotelResearch(
            destination=request.destination,
            check_in_date=request.start_date,
            travelers=request.travelers,
            budget=request.budget,
            currency=request.currency,
            options=[HotelOption(
                name=f"{request.destination} Hotel",
                destination=request.destination,
            )],
        )

    async def activities(request: TripRequest, destination_research):
        calls.append("activity_options")
        return ActivityResearch(
            destination=request.destination,
            options=[ActivityOption(
                name=f"{request.destination} Museum",
                destination=request.destination,
            )],
        )

    async def itinerary(state: TripState):
        calls.append("itinerary")
        request = state.request
        return Itinerary(
            destination=request.destination,
            start_date=request.start_date,
            travelers=request.travelers,
            days=[ItineraryDay(
                day_number=1,
                date=request.start_date,
                items=[ItineraryItem(
                    title=state.activity_options[0].name,
                )],
            )],
        )

    monkeypatch.setattr(
        service.research_service,
        "research_destination",
        destination,
    )
    monkeypatch.setattr(
        service.flight_research_service,
        "research_flights",
        flights,
    )
    monkeypatch.setattr(
        service.hotel_research_service,
        "research_hotels",
        hotels,
    )
    monkeypatch.setattr(
        service.activity_research_service,
        "research_activities",
        activities,
    )
    monkeypatch.setattr(
        service.itinerary_planner_service,
        "build_itinerary",
        itinerary,
    )
    return calls


def set_correction(
    monkeypatch,
    service: ConversationService,
    correction: TripCorrection,
) -> None:
    async def interpret(_message: str) -> TripCorrection:
        return correction

    monkeypatch.setattr(
        service,
        "_interpret_correction",
        interpret,
    )


def test_interest_operations_preserve_unrelated_interests() -> None:
    current = completed_state().request
    applied = apply_correction(
        current,
        TripCorrection(
            interests_add=["museums", "FOOD"],
            interests_remove=["shopping"],
        ),
    )

    assert applied.request.interests == [
        "food",
        "culture",
        "cafés",
        "museums",
    ]
    assert applied.changed_fields == {"interests"}


def test_interest_replace_is_explicit_and_deduplicated() -> None:
    applied = apply_correction(
        completed_state().request,
        TripCorrection(
            interests_replace=["Food", "architecture", "food"],
        ),
    )
    assert applied.request.interests == ["Food", "architecture"]


def test_dependency_graph_matches_real_service_inputs() -> None:
    assert invalidated_artifacts({"origin"}) == (
        "flight_options",
        "itinerary",
    )
    assert invalidated_artifacts({"interests"}) == (
        "activity_options",
        "itinerary",
    )
    assert invalidated_artifacts({"budget"}) == (
        "hotel_options",
        "itinerary",
    )
    assert invalidated_artifacts({"destination"}) == (
        "destination_research",
        "flight_options",
        "hotel_options",
        "activity_options",
        "itinerary",
    )


@pytest.mark.parametrize(
    ("correction", "expected_calls"),
    [
        (
            TripCorrection(origin="Lahore"),
            ["flight_options", "itinerary"],
        ),
        (
            TripCorrection(
                interests_add=["museums"],
                interests_remove=["shopping"],
            ),
            ["activity_options", "itinerary"],
        ),
        (
            TripCorrection(duration_days=8),
            ["hotel_options", "activity_options", "itinerary"],
        ),
        (
            TripCorrection(start_date="2027-10-10"),
            ["flight_options", "hotel_options", "itinerary"],
        ),
        (
            TripCorrection(travelers=3),
            ["hotel_options", "activity_options", "itinerary"],
        ),
        (
            TripCorrection(budget=2000),
            ["hotel_options", "itinerary"],
        ),
        (
            TripCorrection(destination="Istanbul"),
            [
                "destination_research",
                "flight_options",
                "hotel_options",
                "activity_options",
                "itinerary",
            ],
        ),
    ],
)
def test_completed_trip_selectively_replans_only_invalid_artifacts(
    monkeypatch,
    correction: TripCorrection,
    expected_calls: list[str],
) -> None:
    service = ConversationService(state=completed_state())
    calls = install_workflow_spies(monkeypatch, service)
    set_correction(monkeypatch, service, correction)

    asyncio.run(service.process_message("explicit correction"))

    assert calls == expected_calls
    assert service.trip_manager.get_status() == "itinerary_planned"


def test_completed_trip_keeps_same_values_without_replanning(
    monkeypatch,
) -> None:
    service = ConversationService(state=completed_state())
    calls = install_workflow_spies(monkeypatch, service)
    set_correction(
        monkeypatch,
        service,
        TripCorrection(
            destination="seoul",
            travelers=2,
            budget=2500.0,
        ),
    )

    response = asyncio.run(
        service.process_message("Keep it for two people in Seoul.")
    )

    assert calls == []
    assert "couldn't identify" in response
    assert service.trip_manager.get_state() == completed_state()


@pytest.mark.parametrize("message", ["thanks", "Thank you!", "looks good"])
def test_completed_trip_noop_messages_never_interpret_or_replan(
    monkeypatch,
    message: str,
) -> None:
    service = ConversationService(state=completed_state())
    calls = install_workflow_spies(monkeypatch, service)

    async def forbidden(_message: str):
        raise AssertionError("No-op text must not invoke correction inference.")

    monkeypatch.setattr(service, "_interpret_correction", forbidden)
    asyncio.run(service.process_message(message))
    assert calls == []


def test_partial_date_correction_clears_stale_truth_and_waits(
    monkeypatch,
) -> None:
    service = ConversationService(state=completed_state())
    calls = install_workflow_spies(monkeypatch, service)
    set_correction(
        monkeypatch,
        service,
        TripCorrection(start_date_text="October 2028"),
    )

    response = asyncio.run(
        service.process_message("Move it to October 2028.")
    )
    state = service.trip_manager.get_state()

    assert calls == []
    assert state.request.start_date is None
    assert state.request.start_date_text == "October 2028"
    assert state.itinerary is None
    assert state.flight_options == []
    assert state.hotel_options == []
    assert state.destination_research is not None
    assert state.activity_options
    assert state.revision_pending_artifacts == [
        "flight_options",
        "hotel_options",
        "itinerary",
    ]
    assert state.status == "collecting"
    assert "day of the month" in response


def test_partial_date_clarification_resumes_selective_plan(
    monkeypatch,
) -> None:
    service = ConversationService(state=completed_state())
    calls = install_workflow_spies(monkeypatch, service)
    set_correction(
        monkeypatch,
        service,
        TripCorrection(start_date_text="October 2028"),
    )
    asyncio.run(service.process_message("Move it to October 2028."))

    set_correction(monkeypatch, service, TripCorrection())
    asyncio.run(service.process_message("the 15th"))
    state = service.trip_manager.get_state()

    assert state.request.start_date == "2028-10-15"
    assert state.request.start_date_text is None
    assert state.revision_pending_artifacts == []
    assert calls == ["flight_options", "hotel_options", "itinerary"]
    assert state.status == "itinerary_planned"


def test_new_duration_clears_conflicting_explicit_end_date() -> None:
    current = completed_state().request.model_copy(update={
        "end_date": "2027-09-20",
    })
    applied = apply_correction(
        current,
        TripCorrection(duration_days=8),
    )
    assert applied.request.duration_days == 8
    assert applied.request.end_date is None


def test_new_end_date_wins_and_derives_coherent_duration() -> None:
    applied = apply_correction(
        completed_state().request,
        TripCorrection(end_date="2027-09-17"),
    )
    assert applied.request.end_date == "2027-09-17"
    assert applied.request.duration_days == 8
    assert {"end_date", "duration_days"}.issubset(
        applied.changed_fields
    )


def test_failed_replan_keeps_old_persisted_plan_and_retries_same_trip(
    monkeypatch,
) -> None:
    repository = InMemoryTripRepository()
    trip_id = "same-completed-trip"
    original = completed_state()
    repository.create(trip_id, original)
    api_module.session_registry = SessionRegistry(repository=repository)
    client = TestClient(api_module.app)
    attempts: list[str] = []

    async def correction(_service, message: str) -> TripCorrection:
        attempts.append(message)
        return TripCorrection(duration_days=8)

    async def fail_then_finish(service, _artifacts):
        if len(attempts) == 1:
            raise ValueError("planner validation failed")

        restored_artifacts = completed_state()
        state = service.trip_manager.get_state()
        state.hotel_options = restored_artifacts.hotel_options
        state.activity_options = restored_artifacts.activity_options
        state.itinerary = restored_artifacts.itinerary.model_copy(update={
            "end_date": "2027-09-17",
        })
        state.status = "itinerary_planned"
        return "Revised itinerary ready."

    monkeypatch.setattr(
        ConversationService,
        "_interpret_correction",
        correction,
    )
    monkeypatch.setattr(
        ConversationService,
        "_run_selected_artifacts",
        fail_then_finish,
    )

    message = "Make it 8 days."
    failed = client.post(
        f"/trips/{trip_id}/messages",
        json={"message": message},
    )
    assert failed.status_code == 500
    assert repository.get(trip_id) == original

    retried = client.post(
        f"/trips/{trip_id}/messages",
        json={"message": message},
    )
    assert retried.status_code == 200
    assert retried.json()["trip_id"] == trip_id
    assert attempts == [message, message]
    assert repository.get(trip_id).request.duration_days == 8
