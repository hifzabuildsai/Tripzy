import asyncio
import json
from types import SimpleNamespace

from app.models.state import TripState
from app.models.trip import TripRequest
from app.services.conversation import ConversationService
from app.services.trip_manager import TripManager


def test_clarification_lists_all_remaining_requirements():
    manager = TripManager()
    question = manager.get_next_question()

    assert "where you're travelling from" in question
    assert "where you'd like to go" in question
    assert "travel start date" in question
    assert "end date or trip duration" in question
    assert "how many people" in question
    assert "budget and currency" in question
    assert manager.get_missing_information() == [
        "origin", "destination", "start_date",
        "end_date_or_duration", "travelers", "budget",
    ]

    manager.update_request_fields(
        origin="Karachi", destination="Istanbul",
        start_date_text="September 10", duration_days=5,
        travelers=2,
    )
    question = manager.get_next_question()
    assert "year for your travel start date" in question
    assert "budget and currency" in question
    assert "where you're travelling from" not in question


def test_mission_extracts_multiple_fields_and_reasks_only_missing(monkeypatch):
    service = ConversationService()
    prompts = []

    async def fake_run(agent, prompt):
        prompts.append(prompt)
        return SimpleNamespace(new_items=[
            SimpleNamespace(output=json.dumps({
                "origin": "Karachi", "destination": "Istanbul",
                "start_date_text": "September 10", "duration_days": 5,
                "travelers": 2, "interests": ["history", "food"],
                "travel_style": "relaxed", "untrusted_status": "ready",
            })),
        ])

    monkeypatch.setattr("app.services.conversation.Runner.run", fake_run)
    answer = asyncio.run(service.process_message(
        "From Karachi to Istanbul September 10 for 5 days, "
        "two of us, history and food, relaxed pace"
    ))

    request = service.trip_manager.get_state().request
    assert request.origin == "Karachi"
    assert request.destination == "Istanbul"
    assert request.start_date is None
    assert request.start_date_text == "September 10"
    assert request.duration_days == 5
    assert request.travelers == 2
    assert request.interests == ["history", "food"]
    assert request.travel_style == "relaxed"
    assert "year for your travel start date" in answer
    assert "budget and currency" in answer
    assert "how many people" not in answer
    assert "extract every" in prompts[0]


def test_year_reply_also_extracts_other_fields(monkeypatch):
    state = TripState(request=TripRequest(
        origin="Karachi", destination="Istanbul",
        start_date_text="September 10", duration_days=5,
    ))
    service = ConversationService(state=state)
    calls = []

    async def fake_run(agent, prompt):
        calls.append(prompt)
        return SimpleNamespace(new_items=[
            SimpleNamespace(output=json.dumps({"travelers": 2})),
            SimpleNamespace(output=json.dumps({
                "budget": 2000, "currency": "USD",
                "interests": ["history"],
            })),
        ])

    async def stop_before_research():
        return "ready" if service.trip_manager.is_complete() else "incomplete"

    monkeypatch.setattr("app.services.conversation.Runner.run", fake_run)
    monkeypatch.setattr(service, "_continue_workflow", stop_before_research)

    answer = asyncio.run(service.process_message(
        "2027, two travelers, $2000 total; we like history"
    ))
    request = service.trip_manager.get_state().request
    assert answer == "ready"
    assert request.start_date == "2027-09-10"
    assert request.travelers == 2
    assert request.budget == 2000
    assert request.interests == ["history"]
    assert len(calls) == 1
    assert '"start_date": "2027-09-10"' in calls[0]


def test_invalid_year_keeps_date_unresolved(monkeypatch):
    service = ConversationService(state=TripState(request=TripRequest(
        start_date_text="February 29",
    )))

    async def fake_run(agent, prompt):
        return SimpleNamespace(new_items=[])

    monkeypatch.setattr("app.services.conversation.Runner.run", fake_run)
    answer = asyncio.run(service.process_message("2027"))
    assert service.trip_manager.get_state().request.start_date is None
    assert "year for your travel start date" in answer
