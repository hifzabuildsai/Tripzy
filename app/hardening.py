import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from threading import Lock

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


class RequestBodyLimitMiddleware:
    """Reject oversized HTTP request bodies before endpoint processing."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http" or scope.get("method") not in {
            "POST",
            "PUT",
            "PATCH",
        }:
            await self.app(scope, receive, send)
            return

        content_length = _content_length(scope)
        if content_length is not None and content_length > self.max_bytes:
            await _request_too_large(scope, receive, send)
            return

        body = bytearray()
        while True:
            message = await receive()

            if message["type"] == "http.disconnect":
                await self.app(scope, _single_message_receive(message), send)
                return

            body.extend(message.get("body", b""))
            if len(body) > self.max_bytes:
                await _request_too_large(scope, receive, send)
                return

            if not message.get("more_body", False):
                break

        replay = _single_message_receive({
            "type": "http.request",
            "body": bytes(body),
            "more_body": False,
        })
        await self.app(scope, replay, send)


class SecurityHeadersMiddleware:
    """Attach browser-safe headers to every API response."""

    def __init__(self, app: ASGIApp, production: bool) -> None:
        self.app = app
        self.production = production

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    headers[name] = value
                if self.production:
                    headers["Content-Security-Policy"] = (
                        "default-src 'none'; frame-ancestors 'none'"
                    )
                    headers["Strict-Transport-Security"] = (
                        "max-age=31536000; includeSubDomains"
                    )
                else:
                    headers["Content-Security-Policy"] = (
                        "default-src 'self' https://cdn.jsdelivr.net; "
                        "script-src 'self' https://cdn.jsdelivr.net "
                        "'unsafe-inline'; style-src 'self' "
                        "https://cdn.jsdelivr.net 'unsafe-inline'; "
                        "img-src 'self' data:; frame-ancestors 'none'"
                    )
            await send(message)

        await self.app(scope, receive, send_with_headers)


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class FixedWindowRateLimiter:
    """Small process-local write limiter for a single application replica."""

    def __init__(self, request_limit: int, window_seconds: int) -> None:
        self.request_limit = request_limit
        self.window_seconds = window_seconds
        self._windows: dict[str, tuple[float, int]] = {}
        self._lock = Lock()

    def check(self, client_key: str) -> RateLimitDecision:
        now = time.monotonic()

        with self._lock:
            if len(self._windows) > 2_048:
                self._windows = {
                    key: window
                    for key, window in self._windows.items()
                    if now - window[0] < self.window_seconds
                }

            started_at, count = self._windows.get(client_key, (now, 0))
            elapsed = now - started_at

            if elapsed >= self.window_seconds:
                started_at, count = now, 0

            if count >= self.request_limit:
                retry_after = max(1, int(self.window_seconds - elapsed + 0.999))
                return RateLimitDecision(False, retry_after)

            self._windows[client_key] = (started_at, count + 1)
            return RateLimitDecision(True, 0)


class PlanningCapacityError(Exception):
    """Raised when all public-demo planning slots remain occupied."""


class PlanningConcurrencyGuard:
    """Bound simultaneous expensive planning work on one replica."""

    def __init__(self, limit: int, queue_timeout_seconds: float) -> None:
        self.limit = limit
        self.queue_timeout_seconds = queue_timeout_seconds
        self._semaphore = asyncio.BoundedSemaphore(limit)

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.queue_timeout_seconds,
            )
        except TimeoutError as exc:
            raise PlanningCapacityError from exc

        try:
            yield
        finally:
            self._semaphore.release()


def _content_length(scope: Scope) -> int | None:
    for name, value in scope.get("headers", []):
        if name.lower() == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


def _single_message_receive(message: Message) -> Receive:
    delivered = False

    async def receive() -> Message:
        nonlocal delivered
        if not delivered:
            delivered = True
            return message
        return {"type": "http.disconnect"}

    return receive


async def _request_too_large(
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    response = JSONResponse(
        status_code=413,
        content={"detail": "Request body is too large."},
    )
    await response(scope, receive, send)
