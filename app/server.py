import os

import uvicorn

from app.config import validate_production_environment


DEFAULT_PORT = 8000


def get_port() -> int:
    """Return Render's injected port or the local default."""

    raw_port = os.getenv("PORT", str(DEFAULT_PORT))

    try:
        port = int(raw_port)
    except ValueError as exc:
        raise RuntimeError("PORT must be an integer.") from exc

    if not 1 <= port <= 65535:
        raise RuntimeError("PORT must be between 1 and 65535.")

    return port


def main() -> None:
    """Start the production HTTP server on all container interfaces."""

    validate_production_environment()
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=get_port(),
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
