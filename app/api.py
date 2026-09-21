from fastapi import FastAPI, HTTPException
from postgrest.exceptions import APIError

from app.models.api import (
    CreateTripResponse,
    TripMessageRequest,
    TripMessageResponse,
    TripStateResponse,
)
from app.services.session_registry import SessionRegistry


app = FastAPI(
    title="Tripzy API",
    description=(
        "Backend API for Tripzy's agentic travel "
        "planning system."
    ),
    version="0.1.0",
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

    except APIError as exc:
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

    except APIError as exc:
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

    except APIError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Trip persistence service is "
                "temporarily unavailable."
            ),
        ) from exc