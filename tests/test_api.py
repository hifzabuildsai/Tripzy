from fastapi.testclient import TestClient

import app.api as api_module
from app.services.in_memory_trip_repository import (
    InMemoryTripRepository,
)
from app.services.session_registry import SessionRegistry


def build_client() -> TestClient:
    """
    Create an isolated API client backed by an
    in-memory repository.
    """

    api_module.session_registry = SessionRegistry(
        repository=InMemoryTripRepository()
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