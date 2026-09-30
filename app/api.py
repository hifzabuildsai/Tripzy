import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    DEFAULT_MAX_CONCURRENT_PLANNING_REQUESTS,
    DEFAULT_MAX_REQUEST_BODY_BYTES,
    DEFAULT_PLANNING_QUEUE_TIMEOUT_SECONDS,
    DEFAULT_PLANNING_TIMEOUT_SECONDS,
    DEFAULT_PUBLIC_RATE_LIMIT_REQUESTS,
    DEFAULT_PUBLIC_RATE_LIMIT_WINDOW_SECONDS,
    get_api_docs_urls,
    get_cors_origins,
    get_positive_float,
    get_positive_int,
    is_production,
)
from app.hardening import (
    FixedWindowRateLimiter,
    PlanningCapacityError,
    PlanningConcurrencyGuard,
    RequestBodyLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.logging_config import logger
from app.models.api import (
    CreateTripResponse,
    TripMessageRequest,
    TripMessageResponse,
    TripStateResponse,
)
from app.services.session_registry import SessionRegistry
from app.services.trip_repository import TripRepositoryError

app = FastAPI(
    title="Tripzy API",
    description=(
        "Backend API for Tripzy's agentic travel "
        "planning system."
    ),
    version="0.1.0",
    **get_api_docs_urls(),
)


MAX_REQUEST_BODY_BYTES = get_positive_int(
    "MAX_REQUEST_BODY_BYTES",
    DEFAULT_MAX_REQUEST_BODY_BYTES,
)
PUBLIC_RATE_LIMIT_REQUESTS = get_positive_int(
    "PUBLIC_RATE_LIMIT_REQUESTS",
    DEFAULT_PUBLIC_RATE_LIMIT_REQUESTS,
)
PUBLIC_RATE_LIMIT_WINDOW_SECONDS = get_positive_int(
    "PUBLIC_RATE_LIMIT_WINDOW_SECONDS",
    DEFAULT_PUBLIC_RATE_LIMIT_WINDOW_SECONDS,
)
MAX_CONCURRENT_PLANNING_REQUESTS = get_positive_int(
    "MAX_CONCURRENT_PLANNING_REQUESTS",
    DEFAULT_MAX_CONCURRENT_PLANNING_REQUESTS,
)
PLANNING_QUEUE_TIMEOUT_SECONDS = get_positive_float(
    "PLANNING_QUEUE_TIMEOUT_SECONDS",
    DEFAULT_PLANNING_QUEUE_TIMEOUT_SECONDS,
)
PLANNING_TIMEOUT_SECONDS = get_positive_float(
    "PLANNING_TIMEOUT_SECONDS",
    DEFAULT_PLANNING_TIMEOUT_SECONDS,
)


app.add_middleware(
    RequestBodyLimitMiddleware,
    max_bytes=MAX_REQUEST_BODY_BYTES,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.add_middleware(
    SecurityHeadersMiddleware,
    production=is_production(),
)


session_registry = SessionRegistry()
public_rate_limiter = FixedWindowRateLimiter(
    request_limit=PUBLIC_RATE_LIMIT_REQUESTS,
    window_seconds=PUBLIC_RATE_LIMIT_WINDOW_SECONDS,
)
planning_guard = PlanningConcurrencyGuard(
    limit=MAX_CONCURRENT_PLANNING_REQUESTS,
    queue_timeout_seconds=PLANNING_QUEUE_TIMEOUT_SECONDS,
)


def _enforce_public_write_limit(request: Request) -> None:
    client_key = request.client.host if request.client is not None else "unknown"
    decision = public_rate_limiter.check(client_key)

    if decision.allowed:
        return

    logger.warning(
        "public_rate_limit_exceeded",
        extra={
            "status_code": 429,
            "limit": public_rate_limiter.request_limit,
        },
    )
    raise HTTPException(
        status_code=429,
        detail="Too many public demo requests. Please try again shortly.",
        headers={"Retry-After": str(decision.retry_after_seconds)},
    )


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
async def create_trip(request: Request) -> CreateTripResponse:
    """
    Create a new isolated Tripzy planning session.
    """

    _enforce_public_write_limit(request)

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
        logger.warning(
            "trip_persistence_unavailable",
            extra={
                "status_code": 503,
                "error_type": type(exc).__name__,
            },
        )
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
    message_request: TripMessageRequest,
    request: Request,
) -> TripMessageResponse:
    """
    Send one user message to an existing Tripzy
    planning session.
    """

    _enforce_public_write_limit(request)

    try:
        session = session_registry.get_session(
            trip_id
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Trip session not found.",
            )

        try:
            async with planning_guard.slot():
                async with asyncio.timeout(PLANNING_TIMEOUT_SECONDS):
                    response = await session.process_message(
                        message_request.message
                    )
        except PlanningCapacityError as exc:
            logger.warning(
                "planning_capacity_reached",
                extra={
                    "status_code": 503,
                    "limit": MAX_CONCURRENT_PLANNING_REQUESTS,
                },
            )
            raise HTTPException(
                status_code=503,
                detail=(
                    "Tripzy is handling other planning requests. "
                    "Please retry shortly."
                ),
                headers={"Retry-After": "1"},
            ) from exc
        except TimeoutError as exc:
            logger.warning(
                "planning_timeout",
                extra={"status_code": 504},
            )
            raise HTTPException(
                status_code=504,
                detail=(
                    "Tripzy planning timed out. The saved trip is "
                    "unchanged and can be retried."
                ),
            ) from exc

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
            missing_information=(
                session.trip_manager
                .get_missing_information()
            ),
        )

    except HTTPException:
        raise

    except TripRepositoryError as exc:
        logger.warning(
            "trip_persistence_unavailable",
            extra={
                "status_code": 503,
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Trip persistence service is "
                "temporarily unavailable."
            ),
        ) from exc

    except Exception as exc:
        # Each planning request works on state reconstructed from the
        # repository. save_session runs only after process_message
        # succeeds, so a workflow failure must not persist the session's
        # partially mutated in-memory state.
        logger.error(
            "planning_request_failed",
            extra={
                "status_code": 500,
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Tripzy hit a problem while planning this trip. "
                "The saved trip is unchanged and can be retried."
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
            missing_information=(
                session.trip_manager
                .get_missing_information()
            ),
            clarification=(
                session.trip_manager
                .get_next_question()
            ),
        )

    except HTTPException:
        raise

    except TripRepositoryError as exc:
        logger.warning(
            "trip_persistence_unavailable",
            extra={
                "status_code": 503,
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Trip persistence service is "
                "temporarily unavailable."
            ),
        ) from exc
