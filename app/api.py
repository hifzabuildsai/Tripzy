import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.api import (
    CreateTripResponse,
    TripMessageRequest,
    TripMessageResponse,
    TripStateResponse,
)
from app.services.session_registry import SessionRegistry
from app.services.trip_repository import TripRepositoryError


def get_cors_origins() -> list[str]:
    """
    Return the frontend origins allowed to call
    the Tripzy API from a browser.
    """

    configured_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    return [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]


app = FastAPI(
    title="Tripzy API",
    description=(
        "Backend API for Tripzy's agentic travel "
        "planning system."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


session_registry = SessionRegistry()


@app.get("/")
async def root() -> dict[str, str]:
    """
    Basic API root endpoint.
    """

    return {
        "name": "Tripzy API",
        "status": "running",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Lightweight health endpoint.
    """

    return {
        "status": "healthy",
    }


@app.post(
    "/trips",
    response_model=CreateTripResponse,
    status_code=201,
)
async def create_trip() -> CreateTripResponse:
    """
    Create a new isolated Tripzy planning session.
    """

    try:
        trip_id = session_registry.create_session()

        session = session_registry.get_session(
            trip_id
        )

        if session is None:
            raise RuntimeError(
                "Tripzy failed to create the trip session."
            )

        return CreateTripResponse(
            trip_id=trip_id,
            status=(
                session.trip_manager.get_status()
            ),
        )

    except TripRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Trip persistence service is "
                "temporarily unavailable."
            ),
        ) from exc


@app.post(
    "/trips/{trip_id}/messages",
    response_model=TripMessageResponse,
)
async def send_trip_message(
    trip_id: str,
    request: TripMessageRequest,
) -> TripMessageResponse:
    """
    Send one user message to an existing Tripzy
    planning session.
    """

    try:
        session = session_registry.get_session(
            trip_id
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Trip session not found.",
            )

        response = await session.process_message(
            request.message
        )

        session_registry.save_session(
            trip_id=trip_id,
            session=session,
        )

        return TripMessageResponse(
            trip_id=trip_id,
            response=response,
            status=(
                session.trip_manager.get_status()
            ),
        )

    except HTTPException:
        raise

    except TripRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Trip persistence service is "
                "temporarily unavailable."
            ),
        ) from exc


@app.get(
    "/trips/{trip_id}",
    response_model=TripStateResponse,
)
async def get_trip(
    trip_id: str,
) -> TripStateResponse:
    """
    Return the current structured state of an
    existing Tripzy planning session.
    """

    try:
        session = session_registry.get_session(
            trip_id
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Trip session not found.",
            )

        return TripStateResponse(
            trip_id=trip_id,
            state=session.trip_manager.get_state(),
        )

    except HTTPException:
        raise

    except TripRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Trip persistence service is "
                "temporarily unavailable."
            ),
        ) from exc