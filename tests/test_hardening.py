import asyncio
import io
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hardening import (
    PlanningCapacityError,
    PlanningConcurrencyGuard,
    SecurityHeadersMiddleware,
)
from app.logging_config import configure_logging


def test_planning_guard_rejects_work_beyond_capacity() -> None:
    async def scenario() -> None:
        guard = PlanningConcurrencyGuard(
            limit=1,
            queue_timeout_seconds=0.01,
        )

        async with guard.slot():
            with pytest.raises(PlanningCapacityError):
                async with guard.slot():
                    raise AssertionError("The second slot must not be entered.")

        async with guard.slot():
            pass

    asyncio.run(scenario())


def test_production_security_headers_include_hsts() -> None:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, production=True)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    response = TestClient(app).get("/health")

    assert response.headers["strict-transport-security"] == (
        "max-age=31536000; includeSubDomains"
    )
    assert response.headers["content-security-policy"] == (
        "default-src 'none'; frame-ancestors 'none'"
    )


def test_debug_false_suppresses_verbose_and_logging_is_redacted() -> None:
    stream = io.StringIO()
    test_logger = configure_logging(debug=False, stream=stream)

    try:
        test_logger.debug(
            "verbose_event",
            extra={"stage": "planning"},
        )
        test_logger.info(
            "safe_event",
            extra={
                "stage": "planning",
                "request_payload": "do-not-emit",
            },
        )

        lines = stream.getvalue().splitlines()
        assert len(lines) == 1
        payload = json.loads(lines[0])
        assert payload["event"] == "safe_event"
        assert payload["stage"] == "planning"
        assert "do-not-emit" not in lines[0]
    finally:
        configure_logging()
