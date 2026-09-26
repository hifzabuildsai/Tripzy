import json

from fastapi.testclient import TestClient

import app.api as api_module
from app.models.state import TripState
from app.models.trip import TripRequest
from app.services.in_memory_trip_repository import (
    InMemoryTripRepository,
)
from app.services.session_registry import SessionRegistry
from app.services.trip_repository import (
    TripRepository,
    TripRepositoryError,
)


class FailingTripRepository(TripRepository):
    """
    Repository test double that simulates an
    unavailable persistence service.
    """

    def create(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        raise TripRepositoryError(
            "Persistence unavailable."
        )

    def get(
        self,
        trip_id: str,
    ) -> TripState | None:
        raise TripRepositoryError(
            "Persistence unavailable."
        )

    def save(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        raise TripRepositoryError(
            "Persistence unavailable."
        )

    def exists(
        self,
        trip_id: str,
    ) -> bool:
        raise TripRepositoryError(
            "Persistence unavailable."
        )


class JsonRoundTripTripRepository(TripRepository):
    """Repository double that serializes state like JSONB persistence."""

    def __init__(self) -> None:
        self._trips: dict[str, dict] = {}

    def create(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        self._trips[trip_id] = json.loads(
            state.model_dump_json()
        )

    def get(
        self,
        trip_id: str,
    ) -> TripState | None:
        persisted = self._trips.get(trip_id)

        if persisted is None:
            return None

        return TripState.model_validate(
            json.loads(json.dumps(persisted))
        )

    def save(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        self.create(trip_id, state)

    def exists(
        self,
        trip_id: str,
    ) -> bool:
        return trip_id in self._trips


def build_client() -> TestClient:
    """
    Create an isolated API client backed by an
    in-memory repository.
    """

    api_module.session_registry = SessionRegistry(
        repository=InMemoryTripRepository()
    )

    return TestClient(api_module.app)


def build_failing_client() -> TestClient:
    """
    Create an API client whose persistence layer
    intentionally fails.
    """

    api_module.session_registry = SessionRegistry(
        repository=FailingTripRepository()
    )

    return TestClient(api_module.app)


def test_health_endpoint() -> None:
    client = build_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_create_trip() -> None:
    client = build_client()

    response = client.post("/trips")

    assert response.status_code == 201

    body = response.json()

    assert body["trip_id"]
    assert body["status"] == "collecting"


def test_created_trip_can_be_read() -> None:
    client = build_client()

    create_response = client.post("/trips")
    trip_id = create_response.json()["trip_id"]

    response = client.get(
        f"/trips/{trip_id}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["trip_id"] == trip_id
    assert body["state"]["status"] == "collecting"
    assert body["state"]["request"]["origin"] is None
    assert body["state"]["request"]["destination"] is None
    assert body["missing_information"] == [
        "origin",
        "destination",
        "start_date",
        "end_date_or_duration",
        "travelers",
        "budget",
    ]
    assert "everything in one message" in body["clarification"]


def test_message_response_includes_structured_missing_information(
    monkeypatch,
) -> None:
    client = build_client()

    async def fake_process_message(
        conversation,
        user_message: str,
    ) -> str:
        assert user_message == "I want 5 days in Istanbul."
        conversation.trip_manager.update_request_fields(
            destination="Istanbul",
            duration_days=5,
        )
        return conversation.trip_manager.get_next_question()

    monkeypatch.setattr(
        "app.services.conversation.ConversationService.process_message",
        fake_process_message,
    )

    create_response = client.post("/trips")
    trip_id = create_response.json()["trip_id"]

    response = client.post(
        f"/trips/{trip_id}/messages",
        json={
            "message": "I want 5 days in Istanbul.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["trip_id"] == trip_id
    assert body["status"] == "collecting"
    assert body["missing_information"] == [
        "origin",
        "start_date",
        "travelers",
        "budget",
    ]
    assert "everything in one message" in body["response"]

    restored = client.get(f"/trips/{trip_id}").json()
    assert restored["state"]["request"]["destination"] == "Istanbul"
    assert restored["state"]["request"]["duration_days"] == 5
    assert restored["missing_information"] == body["missing_information"]


def test_failed_workflow_is_not_persisted_and_can_retry_same_message(
    monkeypatch,
) -> None:
    repository = JsonRoundTripTripRepository()
    api_module.session_registry = SessionRegistry(
        repository=repository
    )
    client = TestClient(api_module.app)
    message = "Start on September 10."
    attempts: list[str] = []

    async def fail_once_then_succeed(
        conversation,
        user_message: str,
    ) -> str:
        attempts.append(user_message)
        conversation.trip_manager.update_request_fields(
            destination="Istanbul",
        )

        if len(attempts) == 1:
            conversation.trip_manager.set_status(
                "itinerary_planned"
            )
            raise ValueError(
                "Invalid generated itinerary."
            )

        return conversation.trip_manager.get_next_question()

    monkeypatch.setattr(
        "app.services.conversation.ConversationService.process_message",
        fail_once_then_succeed,
    )

    create_response = client.post("/trips")
    trip_id = create_response.json()["trip_id"]
    persisted_before = repository.get(trip_id)

    failed_response = client.post(
        f"/trips/{trip_id}/messages",
        json={"message": message},
        headers={"Origin": "http://localhost:3000"},
    )

    assert failed_response.status_code == 500
    assert failed_response.json() == {
        "detail": (
            "Tripzy hit a problem while planning this trip. "
            "The saved trip is unchanged and can be retried."
        ),
    }
    assert failed_response.headers[
        "access-control-allow-origin"
    ] == "http://localhost:3000"

    persisted_after_failure = repository.get(trip_id)
    assert persisted_after_failure == persisted_before
    assert persisted_after_failure is not None
    assert persisted_after_failure.status == "collecting"
    assert persisted_after_failure.itinerary is None

    retry_response = client.post(
        f"/trips/{trip_id}/messages",
        json={"message": message},
    )

    assert retry_response.status_code == 200
    assert retry_response.json()["trip_id"] == trip_id
    assert attempts == [message, message]
    assert repository.get(trip_id).request.destination == "Istanbul"


def test_month_year_metadata_survives_repository_round_trip() -> None:
    repository = JsonRoundTripTripRepository()
    trip_id = "trip-with-month-and-year"
    repository.create(
        trip_id,
        TripState(request=TripRequest(
            origin="Karachi",
            destination="Istanbul",
            start_date_text="September 2027",
            duration_days=5,
            travelers=2,
            budget=2000,
            currency="USD",
            interests=["history", "food"],
            travel_style="relaxed",
        )),
    )
    api_module.session_registry = SessionRegistry(
        repository=repository
    )
    client = TestClient(api_module.app)

    response = client.get(f"/trips/{trip_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["state"]["request"]["start_date"] is None
    assert body["state"]["request"]["start_date_text"] == (
        "September 2027"
    )
    assert body["missing_information"] == ["start_date_day"]
    assert "day of the month" in body["clarification"]
    assert "year for your travel start date" not in body["clarification"]


def test_missing_trip_returns_404() -> None:
    client = build_client()

    response = client.get(
        "/trips/"
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Trip session not found.",
    }


def test_message_for_missing_trip_returns_404() -> None:
    client = build_client()

    response = client.post(
        (
            "/trips/"
            "00000000-0000-0000-0000-000000000000"
            "/messages"
        ),
        json={
            "message": "Plan a trip to Istanbul.",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Trip session not found.",
    }


def test_empty_message_is_rejected() -> None:
    client = build_client()

    create_response = client.post("/trips")
    trip_id = create_response.json()["trip_id"]

    response = client.post(
        f"/trips/{trip_id}/messages",
        json={
            "message": "",
        },
    )

    assert response.status_code == 422


def test_create_trip_returns_503_when_persistence_fails() -> None:
    client = build_failing_client()

    response = client.post("/trips")

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Trip persistence service is "
            "temporarily unavailable."
        ),
    }


def test_get_trip_returns_503_when_persistence_fails() -> None:
    client = build_failing_client()

    response = client.get(
        "/trips/"
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Trip persistence service is "
            "temporarily unavailable."
        ),
    }


def test_message_returns_503_when_persistence_fails() -> None:
    client = build_failing_client()

    response = client.post(
        (
            "/trips/"
            "00000000-0000-0000-0000-000000000000"
            "/messages"
        ),
        json={
            "message": "Plan a trip to Istanbul.",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Trip persistence service is "
            "temporarily unavailable."
        ),
    }


def test_cors_allows_local_frontend() -> None:
    client = build_client()

    response = client.options(
        "/trips",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:3000"
    )
