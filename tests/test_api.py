from fastapi.testclient import TestClient

import app.api as api_module
from app.models.state import TripState
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